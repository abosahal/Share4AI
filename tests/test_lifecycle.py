from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch, MagicMock
from provider.runtime import LlamaCppAdapter, RuntimeFailure
from provider.app import ProviderApp


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root / 'llama-server.exe'; self.exe.write_bytes(b'test')
        self.model = self.root / 'model.gguf'; self.model.write_bytes(b'GGUF')

    def test_owned_process_loopback_hidden_and_stop(self):
        process = MagicMock(); process.poll.return_value = None
        runtime = LlamaCppAdapter(self.exe)
        with patch('provider.runtime.subprocess.Popen', return_value=process) as launch, patch.object(runtime, 'health', return_value=True):
            runtime.start(self.model, gpu_index=1)
            args, kwargs = launch.call_args
            self.assertEqual(args[0][args[0].index('--host') + 1], '127.0.0.1')
            self.assertIn('--offline', args[0])
            self.assertNotIn('--api-key', args[0])
            self.assertEqual(kwargs['env']['CUDA_VISIBLE_DEVICES'], '1')
            self.assertTrue(kwargs['env']['LLAMA_API_KEY'])
            runtime.stop()
            process.terminate.assert_called_once()
            self.assertIsNone(runtime.process)

    def test_crashed_process_and_cancelled_start(self):
        process = MagicMock(); process.poll.return_value = 1
        runtime = LlamaCppAdapter(self.exe)
        with patch('provider.runtime.subprocess.Popen', return_value=process):
            with self.assertRaises(RuntimeFailure):
                runtime.start(self.model)
        self.assertIsNone(runtime.process)
        event = threading.Event(); event.set()
        with patch('provider.runtime.subprocess.Popen') as launch:
            with self.assertRaises(RuntimeFailure):
                runtime.start(self.model, cancel=event)
            launch.assert_not_called()

    def test_startup_timeout_cleans_process(self):
        process = MagicMock(); process.poll.return_value = None
        runtime = LlamaCppAdapter(self.exe, startup_timeout=0)
        with patch('provider.runtime.subprocess.Popen', return_value=process):
            with self.assertRaises(RuntimeFailure):
                runtime.start(self.model)
        process.terminate.assert_called_once()

    def test_identity_persists_and_settings_do_not_contain_chat(self):
        first = ProviderApp(self.root)
        identity = first.node_id
        first.close()
        second = ProviderApp(self.root)
        self.addCleanup(second.close)
        self.assertEqual(identity, second.node_id)
        self.assertFalse((self.root / 'history.json').exists())

    def test_stop_discards_queued_operations(self):
        app = ProviderApp(self.root)
        self.addCleanup(app.close)
        entered, release, ran = threading.Event(), threading.Event(), threading.Event()
        def blocking():
            entered.set(); release.wait(2)
        app.submit(blocking)
        self.assertTrue(entered.wait(2))
        app.submit(ran.set)
        app.stop_all()
        release.set()
        app.operations.put(None)
        app.worker.join(2)
        self.assertFalse(ran.is_set())
