import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from provider.app import ProviderApp
from provider.hardware import Hardware, GPU
from provider.runtime import LlamaCppAdapter, RuntimeFailure
import test_jobs as job_tests
from test_jobs import FakeRuntime, MODEL
from tools.pilot_control_plane import make_server


class BrowserHTTPTests(unittest.TestCase):
    setUp = job_tests.JobHTTPTests.setUp
    worker = job_tests.JobHTTPTests.worker
    def test_browser_assets_and_authenticated_readiness(self):
        with urllib.request.urlopen(self.url + '/') as response:
            self.assertIn(b'dir="rtl"', response.read())
            self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
        with self.assertRaises(urllib.error.HTTPError) as failure:
            urllib.request.urlopen(self.url + '/v1/client/status')
        self.assertEqual(failure.exception.code, 401)
        failure.exception.close()
        request = urllib.request.Request(self.url + '/v1/client/status',
            headers={'Authorization': 'Bearer client-test-secret'})
        with urllib.request.urlopen(request) as response:
            self.assertEqual(json.load(response), {'ready': True})
        self.server.broker.node['seen'] = 0
        with urllib.request.urlopen(request) as response:
            self.assertEqual(json.load(response), {'ready': False})

    def test_cross_origin_and_rebinding_hosts_rejected(self):
        for headers in ({'Origin': 'https://untrusted.example'}, {'Host': 'untrusted.example'}):
            request = urllib.request.Request(self.url + '/', headers=headers)
            with self.assertRaises(urllib.error.HTTPError) as failure:
                urllib.request.urlopen(request)
            self.assertEqual(failure.exception.code, 403)
            failure.exception.close()

    def test_customer_stream_selects_provider_model(self):
        runtime = FakeRuntime()
        self.worker(runtime)
        request = urllib.request.Request(self.url + '/v1/chat/stream',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'مرحبا'}]}).encode(),
            headers={'Authorization': 'Bearer client-test-secret', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=5) as response:
            events = [json.loads(line[6:]) for line in response if line.startswith(b'data: ')]
        self.assertEqual(''.join(e['text'] for e in events if e['kind'] == 'token'), 'Hello world')
        self.assertEqual(events[-1]['kind'], 'done')
        self.assertEqual(runtime.calls, 1)

    def test_provider_token_cannot_read_client_status(self):
        request = urllib.request.Request(self.url + '/v1/client/status',
            headers={'Authorization': 'Bearer provider-test-secret'})
        with self.assertRaises(urllib.error.HTTPError) as failure:
            urllib.request.urlopen(request)
        self.assertEqual(failure.exception.code, 401)
        failure.exception.close()


class DesktopTrialTests(unittest.TestCase):
    def test_one_click_trial_stream_and_cleanup_without_environment_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            app = ProviderApp(Path(directory))
            runtime = FakeRuntime()
            app.runtime = runtime
            app.record = {'gpu_index': 0, 'runtime_version': 'test',
                'model': {'id': 'test', 'artifact': {'sha256': MODEL}, 'context': 4096}}
            app.result = SimpleNamespace(passed=True, to_dict=lambda: {'passed': True})
            hardware = Hardware('Windows', 'AMD64', 'test', 4, 32768, 24000, 100000,
                [GPU(0, 'test', 8192, 8000, 0, 40)])
            try:
                with patch('provider.app.scan', return_value=hardware), patch('provider.app.webbrowser.open', return_value=True) as browser:
                    app.start_browser_trial()
                    url = browser.call_args.args[0]
                    base, token = url.split('/#access=')
                    request = urllib.request.Request(base + '/v1/client/status',
                        headers={'Authorization': 'Bearer ' + token})
                    ready = False
                    for _ in range(50):
                        with urllib.request.urlopen(request) as response:
                            ready = json.load(response)['ready']
                        if ready:
                            break
                        time.sleep(.05)
                    self.assertTrue(ready)
                    request = urllib.request.Request(base + '/v1/chat/stream',
                        data=json.dumps({'messages': [{'role': 'user', 'content': 'hello'}]}).encode(),
                        headers={'Authorization': 'Bearer ' + token})
                    with urllib.request.urlopen(request, timeout=5) as response:
                        data = response.read()
                    self.assertIn(b'"kind": "done"', data)
                    self.assertIn(b'Hello ', data)
                    self.assertFalse((Path(directory) / 'settings.json').exists())
                    server = app.trial_server
                    app.stop_all()
                    self.assertIsNone(app.trial_client)
                    self.assertIsNone(app.trial_url)
                    self.assertEqual(server.fileno(), -1)
            finally:
                app.close()

    def test_benchmark_required_before_browser_trial(self):
        with tempfile.TemporaryDirectory() as directory:
            app = ProviderApp(Path(directory))
            try:
                with self.assertRaisesRegex(Exception, 'pass benchmark'):
                    app.start_browser_trial()
                self.assertIsNone(app.trial_server)
            finally:
                app.close()

    def test_offload_layer_count_reaches_owned_process(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / 'model.gguf'; model.touch()
            binary = Path(directory) / 'server.exe'; binary.touch()
            process = MagicMock(); process.poll.return_value = None
            runtime = LlamaCppAdapter(binary)
            with patch('provider.runtime.subprocess.Popen', return_value=process) as launch, patch.object(runtime, 'health', return_value=True):
                runtime.start(model, gpu_index=0, gpu_layers=28)
                args = launch.call_args.args[0]
                self.assertEqual(args[args.index('-ngl') + 1], '28')
                runtime.stop()
                runtime.start(model, gpu_layers=28)
                args = launch.call_args.args[0]
                self.assertEqual(args[args.index('-ngl') + 1], '0')
                runtime.stop()
                for invalid in (-1, True, '28', 1000):
                    with self.assertRaises(RuntimeFailure):
                        runtime.start(model, gpu_index=0, gpu_layers=invalid)
