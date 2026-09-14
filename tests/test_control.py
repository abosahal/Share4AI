import threading
import unittest
from provider.control import ControlClient, ControlError, SharingSession, admission
from provider.hardware import GPU
from tools.dev_control_plane import make_server, Registry


class ControlTests(unittest.TestCase):
    def test_remote_http_and_missing_credentials_rejected(self):
        for address in ['http://192.168.1.2:8000', 'https://host.test', 'http://127.0.0.1:8000/path']:
            with self.assertRaises(ControlError):
                ControlClient(address)

    def test_admission_limits(self):
        gpu = GPU(0, 'test', 8000, 4000, 10, 40)
        self.assertEqual(admission(True, True, gpu, 70)[0], 'AVAILABLE')
        for ready, passed, g, limit in [(False, True, gpu, 70), (True, False, gpu, 70),
                                       (True, True, None, 70), (True, True, gpu, 0)]:
            self.assertEqual(admission(ready, passed, g, limit)[0], 'LIMITED')
        gpu.temperature = 85
        self.assertEqual(admission(True, True, gpu, 100)[0], 'LIMITED')
        for limit in [-1, 101, 1.5]:
            with self.assertRaises(ValueError):
                admission(True, True, gpu, limit)

    def test_register_heartbeat_restart_stop_over_http(self):
        registry = Registry()
        server = make_server(0, registry, 'test-token')
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = 'http://127.0.0.1:' + str(server.server_port)
        client = ControlClient(url, 'test-token')
        session = SharingSession(client, 'node-test', lambda: dict(state='LIMITED', capabilities={'accepts_jobs': False}))
        session.enabled = True
        self.assertTrue(session.tick(False))
        self.assertIn('node-test', registry.nodes)
        registry.nodes.clear()  # Simulate Control Plane restart losing ephemeral registration.
        self.assertTrue(session.tick(True))
        session.stop()
        self.assertEqual(registry.snapshot()[0]['state'], 'OFFLINE')
        self.assertFalse(session.enabled)
        with self.assertRaises(ControlError) as error:
            ControlClient(url, 'wrong').post('/v1/nodes/register', {'node_id': 'node'})
        self.assertEqual(error.exception.status, 401)

    def test_stale_lease_excluded(self):
        clock = [0]
        registry = Registry(clock=lambda: clock[0])
        registry.update(dict(node_id='n', sharing_enabled=True), register=True)
        clock[0] = 20
        self.assertEqual(registry.snapshot()[0]['state'], 'OFFLINE')

    def test_stop_cannot_be_followed_by_late_available(self):
        calls = []
        class Client:
            def post(self, path, data):
                calls.append(data['state'])
        session = SharingSession(Client(), 'node', lambda: {'state': 'AVAILABLE'})
        session.enabled = True
        session.stop()
        session.tick(False)
        self.assertEqual(calls, ['OFFLINE'])
