from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import threading
import time
import urllib.request
import urllib.error


class RuntimeFailure(RuntimeError):
    pass


@dataclass
class StreamEvent:
    text: str = ''
    completion_tokens: int | None = None
    tokens_per_second: float | None = None


class RuntimeAdapter(ABC):
    @abstractmethod
    def start(self, model: Path, gpu_index=None, context=4096, cancel=None): ...
    @abstractmethod
    def health(self): ...
    @abstractmethod
    def stream(self, messages, max_tokens=256, cancel=None): ...
    @abstractmethod
    def stop(self): ...


def parse_sse(response):
    """Bound each event and ignore comments; require a completed stream."""
    data = []
    size = 0
    while True:
        line = response.readline(1024 * 1024 + 1)
        if len(line) > 1024 * 1024:
            raise RuntimeFailure('Runtime event too large')
        if not line:
            raise RuntimeFailure('Runtime stream interrupted')
        line = line.decode('utf-8').rstrip('\r\n')
        if line.startswith('data:'):
            data.append(line[5:].lstrip())
            size += len(line)
            if size > 1024 * 1024:
                raise RuntimeFailure('Runtime event too large')
        elif not line and data:
            payload = '\n'.join(data)
            data, size = [], 0
            if payload == '[DONE]':
                return
            item = json.loads(payload)
            if 'error' in item:
                raise RuntimeFailure('Runtime rejected request')
            text = ''.join(choice.get('delta', {}).get('content') or '' for choice in item.get('choices', []))
            tokens = item.get('usage', {}).get('completion_tokens')
            speed = item.get('timings', {}).get('predicted_per_second')
            yield StreamEvent(text, tokens, speed)


class LlamaCppAdapter(RuntimeAdapter):
    def __init__(self, executable: Path, startup_timeout=120):
        self.executable = executable.resolve()
        self.startup_timeout = startup_timeout
        self.process = None
        self.url = ''
        self.key = ''
        self._lock = threading.Lock()
        self._inference = threading.Lock()
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def start(self, model, gpu_index=None, context=4096, cancel=None):
        cancel = cancel or threading.Event()
        if cancel.is_set():
            raise RuntimeFailure('Runtime start cancelled')
        if not 512 <= context <= 8192:
            raise RuntimeFailure('Invalid context size')
        with self._lock:
            if self.process is not None:
                raise RuntimeFailure('Runtime already started; stop before changing model')
            if not self.executable.is_file() or not Path(model).is_file():
                raise RuntimeFailure('Install runtime and model first')
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            self.url = f'http://127.0.0.1:{port}'
            self.key = secrets.token_urlsafe(32)
            # Do not inherit runtime override knobs or credentials from other applications.
            env = {k: v for k, v in os.environ.items() if not k.startswith(('LLAMA_', 'GGML_', 'HF_'))}
            env['LLAMA_API_KEY'] = self.key
            if gpu_index is not None:
                env['CUDA_VISIBLE_DEVICES'] = str(int(gpu_index))
            args = [str(self.executable), '-m', str(Path(model).resolve()), '--host', '127.0.0.1',
                    '--port', str(port), '-c', str(context), '-ngl', '99' if gpu_index is not None else '0',
                    '--parallel', '1', '--log-disable', '--no-webui', '--no-slots', '--offline',
                    '--chat-template-kwargs', '{"enable_thinking":false}', '--timeout', '60']
            self.process = subprocess.Popen(args, cwd=self.executable.parent, env=env,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=0x08000000 if os.name == 'nt' else 0)
        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if cancel.wait(0.2):
                self.stop()
                raise RuntimeFailure('Runtime start cancelled')
            if self.process is None or self.process.poll() is not None:
                self.stop()
                raise RuntimeFailure('Runtime exited; check compatible hardware and runtime package')
            if self.health():
                return
        self.stop()
        raise RuntimeFailure('Runtime startup timed out')

    def health(self):
        if self.process is None or self.process.poll() is not None:
            return False
        try:
            # Unlike /health, /v1/models validates the per-process API key.
            req = urllib.request.Request(self.url + '/v1/models', headers={'Authorization': 'Bearer ' + self.key})
            with self._opener.open(req, timeout=2) as response:
                return bool(json.load(response).get('data'))
        except urllib.error.HTTPError as error:
            error.close()
            return False
        except (OSError, ValueError):
            return False

    def stream(self, messages, max_tokens=256, cancel=None):
        cancel = cancel or threading.Event()
        if not 1 <= max_tokens <= 1024 or not messages or len(messages) > 40:
            raise RuntimeFailure('Invalid inference limits')
        if any(m.get('role') not in ('user', 'assistant', 'system') or not isinstance(m.get('content'), str) for m in messages):
            raise RuntimeFailure('Only text messages are supported')
        if sum(len(m['content']) for m in messages) > 12000:
            raise RuntimeFailure('Conversation too long; start a new chat')
        if not self._inference.acquire(blocking=False):
            raise RuntimeFailure('Runtime busy')
        try:
            if not self.health():
                raise RuntimeFailure('Runtime not ready')
            body = json.dumps(dict(messages=messages, stream=True, max_tokens=max_tokens,
                                   temperature=0, stream_options={'include_usage': True},
                                   chat_template_kwargs={'enable_thinking': False})).encode()
            req = urllib.request.Request(self.url + '/v1/chat/completions', data=body,
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.key})
            deadline = time.monotonic() + 180
            with self._opener.open(req, timeout=30) as response:
                for event in parse_sse(response):
                    if cancel.is_set() or time.monotonic() > deadline:
                        raise RuntimeFailure('Inference cancelled or timed out')
                    yield event
        except urllib.error.HTTPError as error:
            error.close()
            raise RuntimeFailure('Runtime rejected request') from None
        except (OSError, ValueError):
            raise RuntimeFailure('Runtime connection failed') from None
        finally:
            self._inference.release()

    def stop(self):
        with self._lock:
            process, self.process = self.process, None
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            self.key = ''
