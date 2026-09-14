import copy
import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from provider.app import ProviderApp
from provider.hardware import Hardware, GPU
from provider.control import ControlClient
from provider.jobs import JobWorker, JobError, sign_job, verify_job
from provider.runtime import StreamEvent
from tools.pilot_control_plane import Broker, make_server

MODEL = 'a' * 64
TOKEN = 'provider-test-secret'


class JobSecurityTests(unittest.TestCase):
    def job(self):
        return dict(job_id='test-job', node_id='node', model_sha256=MODEL, issued_at=100, expires_at=200,
                    messages=[{'role': 'user', 'content': 'private text'}], max_tokens=32)

    def envelope(self, job):
        return dict(job=job, signature=sign_job(job, TOKEN))

    def test_valid_tampered_expired_wrong_audience_model(self):
        job = self.job()
        self.assertEqual(verify_job(self.envelope(job), TOKEN, 'node', MODEL, 150), job)
        bad = self.envelope(job); bad['job'] = copy.deepcopy(job); bad['job']['messages'][0]['content'] = 'tampered'
        with self.assertRaises(JobError): verify_job(bad, TOKEN, 'node', MODEL, 150)
        for node, model, now in [('other', MODEL, 150), ('node', 'b'*64, 150), ('node', MODEL, 201)]:
            with self.assertRaises(JobError): verify_job(self.envelope(job), TOKEN, node, model, now)
        with self.assertRaises(JobError): verify_job(self.envelope(job), 'wrong', 'node', MODEL, 150)

    def test_invalid_deadlines_and_message_limits(self):
        for field, value in [('expires_at', float('inf')), ('expires_at', 400), ('issued_at', 190), ('max_tokens', 5000),
                             ('messages', [{'role': 'user', 'content': 'x' * 12001}])]:
            job = self.job(); job[field] = value
            with self.assertRaises((JobError, ValueError)):
                verify_job(self.envelope(job), TOKEN, 'node', MODEL, 150)

    def broker(self):
        broker = Broker(TOKEN, clock=lambda: 100)
        broker.register(dict(node_id='node', sharing_enabled=True, state='AVAILABLE',
                             capabilities={'accepts_jobs': True, 'model_sha256': MODEL}), True)
        return broker

    def test_claim_once_sequence_and_terminal_replay(self):
        broker = self.broker()
        identity = broker.submit(self.job()['messages'], 32, MODEL)
        code, result = broker.provider_request('/v1/jobs/poll', {'node_id': 'node'})
        self.assertEqual(code, 200)
        self.assertIsNone(broker.provider_request('/v1/jobs/poll', {'node_id': 'node'})[1]['envelope'])
        payload = dict(node_id='node', job_id=identity, signature=result['envelope']['signature'], sequence=1, kind='token', text='a')
        self.assertEqual(broker.provider_request('/v1/jobs/event', payload)[0], 409)
        payload['sequence'] = 0
        self.assertEqual(broker.provider_request('/v1/jobs/event', payload)[0], 200)
        self.assertEqual(broker.provider_request('/v1/jobs/event', payload)[0], 409)
        payload.update(sequence=1, kind='done', text='')
        self.assertEqual(broker.provider_request('/v1/jobs/event', payload)[0], 200)
        self.assertEqual(broker.provider_request('/v1/jobs/event', payload)[0], 409)
        self.assertEqual(broker.jobs[identity]['job']['messages'], [])

    def test_stale_provider_and_stop_cancel(self):
        broker = self.broker()
        identity = broker.submit(self.job()['messages'], 32, MODEL)
        broker.register(dict(node_id='node', sharing_enabled=False), False)
        self.assertTrue(broker.jobs[identity]['terminal'])
        with self.assertRaises(JobError): broker.submit(self.job()['messages'], 32, MODEL)
        broker = self.broker(); broker.clock = lambda: 121
        with self.assertRaises(JobError): broker.submit(self.job()['messages'], 32, MODEL)

    def test_credential_binding_and_wrong_event_signature(self):
        broker = self.broker()
        self.assertEqual(broker.register({'node_id': 'other'}, True)[0], 403)
        self.assertEqual(broker.provider_request('/v1/jobs/poll', {'node_id': 'other'})[0], 403)
        identity = broker.submit(self.job()['messages'], 32, MODEL)
        broker.provider_request('/v1/jobs/poll', {'node_id': 'node'})
        self.assertEqual(broker.provider_request('/v1/jobs/status', dict(node_id='node', job_id=identity, signature='wrong'))[0], 403)


class FakeRuntime:
    def __init__(self, block=False):
        self.entered = threading.Event()
        self.stopped = threading.Event()
        self.block = block
        self.calls = 0

    def stream(self, messages, max_tokens=256, cancel=None):
        self.calls += 1
        self.entered.set()
        yield StreamEvent('Hello ')
        if self.block:
            self.stopped.wait(5)
            if self.stopped.is_set():
                raise RuntimeError('stopped')
        yield StreamEvent('world')

    def stop(self):
        self.stopped.set()

    def health(self):
        return not self.stopped.is_set()


class JobHTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server(TOKEN, 'client-test-secret', 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)
        self.client = ControlClient(self.url, TOKEN)
        self.client.post('/v1/nodes/register', dict(node_id='node', sharing_enabled=True, state='AVAILABLE',
                         capabilities={'accepts_jobs': True, 'model_sha256': MODEL}))

    def worker(self, runtime):
        worker = JobWorker(self.client, 'node', runtime, lambda: True, lambda: MODEL, interval=0.02)
        worker.start(); self.addCleanup(worker.stop)
        return worker

    def chat(self, credential='client-test-secret'):
        req = urllib.request.Request(self.url + '/v1/chat/stream', data=json.dumps(dict(
            messages=[{'role': 'user', 'content': 'private prompt'}], model_sha256=MODEL, max_tokens=32)).encode(),
            headers={'Authorization': 'Bearer ' + credential, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=8) as response:
            return [json.loads(line[6:]) for line in response if line.startswith(b'data: ')]

    def test_end_to_end_stream_and_no_runtime_stop_on_success(self):
        runtime = FakeRuntime(); self.worker(runtime)
        events = self.chat()
        self.assertEqual(''.join(e['text'] for e in events if e['kind'] == 'token'), 'Hello world')
        self.assertEqual(events[-1]['kind'], 'done')
        self.assertFalse(runtime.stopped.is_set())
        self.assertEqual(runtime.calls, 1)

    def test_stop_cancels_mid_stream(self):
        runtime = FakeRuntime(block=True); worker = self.worker(runtime)
        result = []
        request = threading.Thread(target=lambda: result.extend(self.chat())); request.start()
        self.assertTrue(runtime.entered.wait(3))
        started = time.monotonic(); worker.stop()
        request.join(5)
        self.assertFalse(request.is_alive())
        self.assertLess(time.monotonic() - started, 4)
        self.assertTrue(runtime.stopped.is_set())
        self.assertEqual(result[-1]['kind'], 'error')
        self.assertNotIn('world', ''.join(e['text'] for e in result))

    def test_client_and_provider_credentials_are_not_interchangeable(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.chat(TOKEN)
        self.assertEqual(caught.exception.code, 401); caught.exception.close()

    def test_disconnect_control_plane_stops_active_inference(self):
        runtime = FakeRuntime(block=True); worker = self.worker(runtime)
        result = []
        request = threading.Thread(target=lambda: result.extend(self.chat())); request.start()
        self.assertTrue(runtime.entered.wait(3))
        # Simulate restart: outstanding job lease disappears; status returns 403.
        with self.server.broker.condition:
            for item in self.server.broker.jobs.values():
                self.server.broker.terminal(item, 'error', 'restart')
        self.assertTrue(runtime.stopped.wait(3))
        request.join(5)
        self.assertEqual(result[-1]['kind'], 'error')

    def test_worker_rejects_replayed_job_without_second_inference(self):
        runtime = FakeRuntime()
        worker = JobWorker(self.client, 'node', runtime, lambda: True, lambda: MODEL)
        identity = self.server.broker.submit([{'role': 'user', 'content': 'a'}], 32, MODEL)
        env = self.client.post('/v1/jobs/poll', {'node_id': 'node'})['envelope']
        worker.execute(env)
        with self.assertRaises(JobError): worker.execute(env)
        self.assertEqual(runtime.calls, 1)

    def test_desktop_controller_shares_without_exposing_customer_text(self):
        with tempfile.TemporaryDirectory() as temp:
            app = ProviderApp(Path(temp))
            app.node_id = 'node'
            app.runtime = FakeRuntime()
            app.record = dict(gpu_index=0, runtime_version='test',
                              model=dict(id='test', context=4096, artifact={'sha256': MODEL}))
            app.result = SimpleNamespace(passed=True, to_dict=lambda: {})
            app.settings['control_plane'] = self.url
            hw = Hardware('Windows', 'AMD64', 'CPU', 8, 32000, 16000, 50000,
                          [GPU(0, 'test', 12000, 10000, 10, 40)])
            try:
                with patch('provider.app.scan', return_value=hw), patch.dict('os.environ', {'SHARE4AI_PROVIDER_TOKEN': TOKEN}):
                    app.start_sharing()
                    deadline = time.monotonic() + 3
                    while not app.sharing.connected and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertTrue(app.sharing.connected)
                    events = self.chat()
                    self.assertEqual(events[-1]['kind'], 'done')
                    desktop_events = []
                    while not app.events.empty(): desktop_events.append(app.events.get())
                    self.assertFalse(any(kind in ('token', 'answer') for kind, _ in desktop_events))
                    app.stop_sharing()
                    self.assertFalse(app.snapshot()['capabilities']['accepts_jobs'])
            finally:
                app.close()
