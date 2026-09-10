"""Versioned outbound registration. Never sends chat messages."""
import json
import math
import threading
import urllib.error
import urllib.parse
import urllib.request
from . import __version__


class ControlError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ControlError('Control Plane redirects are not allowed')


class ControlClient:
    def __init__(self, base_url, token=''):
        p = urllib.parse.urlsplit(base_url)
        if (p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password
                or p.query or p.fragment or p.path not in ('', '/')):
            raise ControlError('Invalid Control Plane address')
        if p.scheme == 'http' and p.hostname not in ('127.0.0.1', 'localhost', '::1'):
            raise ControlError('HTTP is allowed only for local development')
        if p.scheme == 'https' and not token:
            raise ControlError('A provider credential is required for remote registration')
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect(), urllib.request.ProxyHandler({}))

    def post(self, path, payload):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        request = urllib.request.Request(self.base_url + path, data=json.dumps(payload, allow_nan=False).encode(), headers=headers)
        try:
            with self.opener.open(request, timeout=5) as response:
                data = response.read(65537)
                if len(data) > 65536:
                    raise ControlError('Control Plane response too large')
                result = json.loads(data)
                if not isinstance(result, dict) or result.get('node_id') != payload['node_id']:
                    raise ControlError('Invalid registration acknowledgment')
                return result
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            raise ControlError('Control Plane rejected request', status) from None
        except (OSError, ValueError):
            raise ControlError('Control Plane unavailable') from None


def admission(runtime_ready, benchmark_passed, gpu, maximum, busy=False):
    if not isinstance(maximum, int) or not 0 <= maximum <= 100:
        raise ValueError('Max GPU Usage must be an integer from 0 to 100')
    if not runtime_ready:
        return 'LIMITED', 'Runtime not ready'
    if busy:
        return 'BUSY', 'Local AI has priority'
    if not benchmark_passed:
        return 'LIMITED', 'Benchmark has not passed'
    if maximum == 0:
        return 'LIMITED', 'Owner limit is zero'
    if gpu is None or gpu.utilization is None or gpu.temperature is None:
        return 'LIMITED', 'GPU telemetry unavailable'
    if not all(math.isfinite(x) for x in [gpu.utilization, gpu.temperature]):
        return 'LIMITED', 'Invalid GPU telemetry'
    if gpu.temperature >= 80 or gpu.utilization >= maximum:
        return 'LIMITED', 'Owner resource limit reached'
    return 'AVAILABLE', 'Resource checks passed'


class SharingSession:
    def __init__(self, client, node_id, snapshot, on_status=lambda state: None, interval=5):
        self.client, self.node_id, self.snapshot = client, node_id, snapshot
        self.on_status, self.interval = on_status, interval
        self.enabled = False
        self.connected = False
        self._stop = threading.Event()
        self._thread = None
        self._wire = threading.Lock()

    def payload(self, offline=False):
        data = self.snapshot()
        state = data.pop('state')
        return dict(node_id=self.node_id, protocol_version='1.1', app_version=__version__,
                    sharing_enabled=not offline and self.enabled, state='OFFLINE' if offline else state, **data)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self.enabled = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def tick(self, registered):
        with self._wire:
            if self._stop.is_set():
                return False
            payload = self.payload()
            if not registered:
                self.client.post('/v1/nodes/register', payload)
            try:
                self.client.post('/v1/nodes/heartbeat', payload)
            except ControlError as error:
                if error.status != 404:
                    raise
                self.client.post('/v1/nodes/register', payload)
                self.client.post('/v1/nodes/heartbeat', payload)
            self.connected = True
            self.on_status(payload['state'])
            return True

    def _run(self):
        registered, delay = False, self.interval
        while not self._stop.is_set():
            try:
                registered = self.tick(registered)
                delay = self.interval
            except Exception:
                # Do not expose transport bodies or credentials in diagnostics.
                self.connected = False
                registered = False
                self.on_status('CONTROL PLANE OFFLINE')
                delay = min(max(delay * 2, self.interval), 30)
            self._stop.wait(delay)

    def stop(self):
        self.enabled = False  # Local admission is disabled before waiting on the network.
        self._stop.set()
        self.connected = False
        with self._wire:
            try:
                self.client.post('/v1/nodes/heartbeat', self.payload(offline=True))
            except Exception:
                pass  # Server lease expires if offline notification cannot be delivered.
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=6)
        self.on_status('OFFLINE')
