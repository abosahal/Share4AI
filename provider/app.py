"""Desktop controller with a serial operation queue; UI access remains on Tk thread."""
import json
import os
from pathlib import Path
import queue
import threading
import uuid
from .hardware import scan
from .catalog import recommend
from .provision import install, atomic_json, verify_install
from .runtime import LlamaCppAdapter
from .benchmark import benchmark
from .control import ControlClient, SharingSession, admission


class ProviderApp:
    def __init__(self, root=None):
        self.root = Path(root or Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Share4AI')
        self.root.mkdir(parents=True, exist_ok=True)
        self.events = queue.Queue()
        self.operations = queue.Queue()
        self.cancel = threading.Event()
        self.closed = False
        self.runtime = None
        self.sharing = None
        self.hardware = None
        self.recommendation = None
        self.result = None
        self.record = self._read('installed.json', None)
        self.settings = self._read('settings.json', dict(control_plane='http://127.0.0.1:8000', maximum=70))
        self.node_id = self._read('identity.json', {}).get('node_id') or str(uuid.uuid4())
        atomic_json(self.root / 'identity.json', dict(node_id=self.node_id))
        self.busy = False
        self.worker = threading.Thread(target=self._work, daemon=True)
        self.worker.start()

    def _read(self, name, default):
        try:
            return json.loads((self.root / name).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return default

    def emit(self, kind, value):
        self.events.put((kind, value))

    def submit(self, action):
        if not self.closed:
            self.operations.put(action)

    def _work(self):
        while True:
            action = self.operations.get()
            if action is None:
                return
            if self.closed:
                continue
            self.cancel.clear()
            self.emit('working', True)
            try:
                action()
            except Exception as error:
                # Only application-owned safe error strings; unknown exception details may contain paths/content.
                from .runtime import RuntimeFailure
                from .artifacts import ArtifactError
                from .control import ControlError
                message = str(error) if isinstance(error, (RuntimeFailure, ArtifactError, ControlError)) else 'Operation failed; check device and settings, then retry'
                self.emit('status', message)
            finally:
                self.emit('working', False)

    def scan_device(self):
        self.hardware = scan(self.root)
        self.recommendation = recommend(self.hardware)
        self.emit('hardware', self.hardware)
        self.emit('recommendation', self.recommendation)

    def provision(self):
        if self.sharing and self.sharing.enabled:
            self.stop_sharing()
        if self.runtime:
            self.runtime.stop()
            self.runtime = None
        self.result = None
        self.scan_device()
        self.record = install(self.root, self.recommendation, self.cancel, lambda m: self.emit('status', m))

    def start_local(self):
        if not self.record:
            raise RuntimeError('Install first')
        if self.runtime and self.runtime.health():
            self.emit('status', 'Local AI ready')
            return
        self.result = None
        if self.runtime:
            self.runtime.stop()
        self.emit('status', 'Verifying installed files')
        binary, model = verify_install(self.root, self.record)
        self.runtime = LlamaCppAdapter(binary)
        self.emit('status', 'Starting local model')
        self.runtime.start(model, self.record['gpu_index'], self.record['model']['context'], self.cancel)
        self.emit('status', 'Local AI ready — benchmark required for sharing')

    def run_benchmark(self):
        self.result = None
        self.start_local()
        self.busy = True
        try:
            self.emit('status', 'Benchmark: warmup + three Arabic/English samples')
            self.result = benchmark(self.runtime, self.record['model'], self.record['runtime_version'], self.cancel)
            atomic_json(self.root / 'benchmark.json', self.result.to_dict())
            self.emit('benchmark', self.result)
        finally:
            self.busy = False

    def chat(self, messages):
        self.busy = True
        try:
            self.start_local()
            answer = ''
            for event in self.runtime.stream(messages, cancel=self.cancel):
                if event.text:
                    answer += event.text
                    self.emit('token', event.text)
            self.emit('answer', answer)
        finally:
            self.busy = False

    def snapshot(self):
        hardware = scan(self.root)
        gpu = next((g for g in hardware.gpus if self.record and g.index == self.record['gpu_index']), None)
        state, reason = admission(bool(self.runtime and self.runtime.health()), bool(self.result and self.result.passed),
                                  gpu, int(self.settings['maximum']), self.busy)
        # Sprint 1 advertises discovery only. A router must never dispatch jobs to this alpha.
        if state == 'AVAILABLE':
            state, reason = 'LIMITED', 'Job transport is scheduled for Sprint 2'
        capabilities = dict(runtime='llama.cpp', runtime_version=self.record['runtime_version'] if self.record else None,
            model_id=self.record['model']['id'] if self.record else None,
            model_sha256=self.record['model']['artifact']['sha256'] if self.record else None,
            context=self.record['model']['context'] if self.record else 0, max_concurrency=1,
            accepts_jobs=False, local_ai=True)
        return dict(state=state, reason=reason, max_gpu_usage=self.settings['maximum'],
                    capabilities=capabilities, telemetry=dict(utilization=gpu.utilization if gpu else None,
                        temperature=gpu.temperature if gpu else None, free_vram_mb=gpu.free_mb if gpu else None),
                    benchmark=self.result.to_dict() if self.result else None)

    def start_sharing(self):
        if self.sharing and self.sharing.enabled:
            return
        client = ControlClient(self.settings['control_plane'], os.environ.get('SHARE4AI_PROVIDER_TOKEN', ''))
        self.sharing = SharingSession(client, self.node_id, self.snapshot, lambda s: self.emit('sharing', s))
        self.sharing.start()
        self.emit('status', 'Registration enabled; network jobs are not enabled in this alpha')

    def stop_sharing(self):
        if self.sharing:
            self.sharing.stop()

    def save_settings(self, address, maximum):
        ControlClient(address, os.environ.get('SHARE4AI_PROVIDER_TOKEN', ''))
        if not 0 <= maximum <= 100:
            raise ValueError('Invalid maximum')
        self.stop_sharing()
        self.settings = dict(control_plane=address, maximum=maximum)
        atomic_json(self.root / 'settings.json', self.settings)
        self.emit('status', 'Settings saved; sharing stopped')

    def stop_all(self):
        self.cancel.set()
        if self.sharing:
            self.sharing.enabled = False
        if self.runtime:
            self.runtime.stop()
        self.result = None
        self.stop_sharing()
        self.emit('status', 'Stopped')

    def close(self):
        self.closed = True
        self.stop_all()
        self.operations.put(None)
