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
from .jobs import JobWorker, JobError


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
        self.jobs = None
        self._inference_slot = threading.Lock()
        self._sharing_lock = threading.RLock()
        self.hardware = None
        self.recommendation = None
        self.result = None
        self.record = self._read('installed.json', None)
        self.settings = self._read('settings.json', dict(control_plane='http://127.0.0.1:8000', maximum=70))
        self.node_id = self._read('identity.json', {}).get('node_id') or str(uuid.uuid4())
        atomic_json(self.root / 'identity.json', dict(node_id=self.node_id))
        self.busy = False
        self._operation_lock = threading.Lock()
        self._generation = 0
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
            self.operations.put((self._generation, action))

    def _work(self):
        while True:
            item = self.operations.get()
            if item is None:
                return
            generation, action = item
            with self._operation_lock:
                if self.closed or generation != self._generation:
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
                message = str(error) if isinstance(error, (RuntimeFailure, ArtifactError, ControlError, JobError)) else 'Operation failed; check device and settings, then retry'
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
        if self.cancel.is_set():
            from .runtime import RuntimeFailure
            raise RuntimeFailure('Start cancelled')
        self.runtime = LlamaCppAdapter(binary)
        self.emit('status', 'Starting local model')
        self.runtime.start(model, self.record['gpu_index'], self.record['model']['context'], self.cancel)
        self.emit('status', 'Local AI ready — benchmark required for sharing')

    def run_benchmark(self):
        self.stop_sharing()
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
        self.stop_sharing()  # Owner local use cancels remote work before touching runtime.
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
                                  gpu, int(self.settings['maximum']), self.busy or bool(self.jobs and self.jobs.active))
        transport_ready = bool(self.jobs and not self.jobs.stopping.is_set())
        if state == 'AVAILABLE' and not transport_ready:
            state, reason = 'LIMITED', 'Job worker not running'
        capabilities = dict(runtime='llama.cpp', runtime_version=self.record['runtime_version'] if self.record else None,
            model_id=self.record['model']['id'] if self.record else None,
            model_sha256=self.record['model']['artifact']['sha256'] if self.record else None,
            context=self.record['model']['context'] if self.record else 0, max_concurrency=1,
            accepts_jobs=transport_ready, local_ai=True)
        return dict(state=state, reason=reason, max_gpu_usage=self.settings['maximum'],
                    capabilities=capabilities, telemetry=dict(utilization=gpu.utilization if gpu else None,
                        temperature=gpu.temperature if gpu else None, free_vram_mb=gpu.free_mb if gpu else None),
                    benchmark=self.result.to_dict() if self.result else None)

    def start_sharing(self):
        with self._sharing_lock:
            if self.cancel.is_set() or self.closed:
                return
            if self.sharing and self.sharing.enabled:
                return
            if not self.runtime or not self.runtime.health() or not self.result or not self.result.passed:
                raise JobError('Start Local AI and pass benchmark before sharing')
            client = ControlClient(self.settings['control_plane'], os.environ.get('SHARE4AI_PROVIDER_TOKEN', ''))
            self.sharing = SharingSession(client, self.node_id, self.snapshot, lambda s: self.emit('sharing', s))
            self.jobs = JobWorker(client, self.node_id, self.runtime,
                lambda: self.sharing.enabled and self.sharing.connected and self.snapshot()['state'] == 'AVAILABLE',
                lambda: self.record['model']['artifact']['sha256'], slot=self._inference_slot)
            self.sharing.start()
            self.jobs.start()
            self.emit('status', 'Sharing started; jobs run only while device is eligible')

    def stop_sharing(self):
        with self._sharing_lock:
            if self.sharing:
                self.sharing.enabled = False
            if self.jobs:
                self.jobs.stop()
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
        with self._operation_lock:
            self._generation += 1
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
