"""Outbound, single-slot job execution. Customer text never reaches desktop events."""
import hashlib
import hmac
import json
import threading
import time


class JobError(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def sign_job(job, credential):
    return hmac.new(credential.encode(), b'Share4AI-job-v1\0' + canonical(job), hashlib.sha256).hexdigest()


def validate_messages(messages, maximum):
    if type(maximum) is not int or not 1 <= maximum <= 1024:
        raise JobError('Invalid output limit')
    if not isinstance(messages, list) or not 1 <= len(messages) <= 40:
        raise JobError('Invalid messages')
    if any(not isinstance(m, dict) or set(m) != {'role', 'content'} or
           m['role'] not in ('system', 'user', 'assistant') or not isinstance(m['content'], str) for m in messages):
        raise JobError('Text messages only')
    if sum(len(m['content']) for m in messages) > 12000:
        raise JobError('Context limit exceeded')


def verify_job(envelope, credential, node_id, model_sha256, now=None):
    now = time.time() if now is None else now
    if not credential or not isinstance(envelope, dict):
        raise JobError('Missing job authorization')
    job = envelope.get('job')
    signature = envelope.get('signature')
    if not isinstance(job, dict) or not isinstance(signature, str) or not hmac.compare_digest(sign_job(job, credential), signature):
        raise JobError('Invalid job authorization')
    if set(job) != {'job_id', 'node_id', 'model_sha256', 'issued_at', 'expires_at', 'messages', 'max_tokens'}:
        raise JobError('Invalid job schema')
    if job['node_id'] != node_id or job['model_sha256'] != model_sha256:
        raise JobError('Job audience or model mismatch')
    issued, expiry = job['issued_at'], job['expires_at']
    if (type(issued) not in (int, float) or type(expiry) not in (int, float)
            or not now - 180 <= issued <= now + 5 or not now < expiry <= issued + 180):
        raise JobError('Expired or invalid job deadline')
    if not isinstance(job['job_id'], str) or not 1 <= len(job['job_id']) <= 64:
        raise JobError('Invalid job identity')
    validate_messages(job['messages'], job['max_tokens'])
    return job


class JobWorker:
    def __init__(self, client, node_id, runtime, eligible, model_hash, slot=None, interval=0.5):
        if not client.token:
            raise JobError('Provider credential required for jobs')
        self.client, self.node_id, self.runtime = client, node_id, runtime
        self.eligible, self.model_hash = eligible, model_hash
        self.slot = slot or threading.Lock()
        self.interval = interval
        self.stopping = threading.Event()
        self.cancel = threading.Event()
        self.active = False
        self._gate = threading.Lock()
        self._thread = None
        self.seen = {}

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _post(self, path, **payload):
        return self.client.post(path, dict(node_id=self.node_id, **payload))

    def _run(self):
        while not self.stopping.is_set():
            try:
                if self.eligible():
                    result = self._post('/v1/jobs/poll')
                    if result.get('envelope'):
                        self.execute(result['envelope'])
            except Exception:
                # Generic failure only; no request bodies, keys or exception text in logs.
                self.stopping.wait(2)
            self.stopping.wait(self.interval)

    def execute(self, envelope):
        job = verify_job(envelope, self.client.token, self.node_id, self.model_hash())
        self.seen = {key: expiry for key, expiry in self.seen.items() if expiry > time.time()}
        if job['job_id'] in self.seen:
            raise JobError('Replayed job')
        self.seen[job['job_id']] = job['expires_at']
        if not self.slot.acquire(blocking=False):
            self._post('/v1/jobs/event', job_id=job['job_id'], signature=envelope['signature'],
                       sequence=0, kind='error', text='provider_busy')
            return
        sequence = 0
        monitor_done = threading.Event()
        def send(kind, text=''):
            nonlocal sequence
            self._post('/v1/jobs/event', job_id=job['job_id'], signature=envelope['signature'],
                       sequence=sequence, kind=kind, text=text)
            sequence += 1
        def monitor():
            while not monitor_done.wait(0.25):
                try:
                    cancelled = self._post('/v1/jobs/status', job_id=job['job_id'], signature=envelope['signature']).get('cancelled', True)
                    if cancelled or time.time() >= job['expires_at']:
                        self.cancel.set()
                        self.runtime.stop()  # Interrupt even a blocked read / long prompt prefill.
                        return
                except Exception:
                    self.cancel.set()
                    self.runtime.stop()
                    return
        watcher = None
        try:
            with self._gate:
                if self.stopping.is_set() or not self.eligible():
                    send('error', 'provider_unavailable')
                    return
                self.cancel.clear()
                self.active = True
            watcher = threading.Thread(target=monitor, daemon=True)
            watcher.start()
            for event in self.runtime.stream(job['messages'], max_tokens=job['max_tokens'], cancel=self.cancel):
                if self.cancel.is_set() or self.stopping.is_set():
                    raise JobError('Job cancelled')
                if event.text:
                    send('token', event.text)
            if self.cancel.is_set() or self.stopping.is_set():
                raise JobError('Job cancelled')
            monitor_done.set()
            watcher.join(timeout=6)
            if self.cancel.is_set() or self.stopping.is_set():
                raise JobError('Job cancelled')
            send('done')
        except Exception:
            self.cancel.set()
            self.runtime.stop()
            try:
                send('error', 'cancelled' if self.stopping.is_set() else 'inference_failed')
            except Exception:
                pass
        finally:
            monitor_done.set()
            if watcher:
                watcher.join(timeout=6)
            with self._gate:
                self.active = False
            self.slot.release()

    def stop(self):
        with self._gate:
            self.stopping.set()
            self.cancel.set()
            if self.active:
                self.runtime.stop()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=12)
