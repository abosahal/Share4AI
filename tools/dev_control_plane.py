"""Loopback-only protocol fixture, not a production control plane or job router."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading
import time


class Registry:
    def __init__(self, clock=time.monotonic, ttl=20):
        self.nodes = {}
        self.lock = threading.Lock()
        self.clock, self.ttl = clock, ttl

    def update(self, payload, register=False):
        with self.lock:
            identity = payload.get('node_id')
            if not isinstance(identity, str) or not 1 <= len(identity) <= 100:
                return 400, {'error': 'invalid_node_id'}
            if not register and identity not in self.nodes:
                return 404, {'error': 'registration_required'}
            # This fixture never dispatches jobs, even if a client advertises AVAILABLE.
            state = 'OFFLINE' if not payload.get('sharing_enabled') else 'LIMITED'
            self.nodes[identity] = dict(payload, state=state, seen=self.clock())
            return 200, dict(node_id=identity, heartbeat_interval_seconds=5, lease_seconds=self.ttl, accepts_jobs=False)

    def snapshot(self):
        with self.lock:
            return [dict(node_id=k, state='OFFLINE' if self.clock() - n['seen'] >= self.ttl else n['state'],
                         capabilities=n.get('capabilities', {})) for k, n in self.nodes.items()]


def make_server(port=8000, registry=None, token=''):
    registry = registry or Registry()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, code, value):
            data = json.dumps(value).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == '/health':
                self.send(200, {'status': 'ok', 'mode': 'local-protocol-fixture'})
            elif self.path == '/v1/nodes':
                self.send(200, registry.snapshot())
            else:
                self.send(404, {'error': 'not_found'})

        def do_POST(self):
            self.connection.settimeout(5)
            if token and not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
                self.send(401, {'error': 'unauthorized'}); return
            if self.path not in ('/v1/nodes/register', '/v1/nodes/heartbeat'):
                self.send(404, {'error': 'not_found'}); return
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 65536:
                    self.send(413, {'error': 'payload_limit'}); return
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError()
                code, result = registry.update(payload, self.path.endswith('/register'))
                self.send(code, result)
            except (ValueError, OSError):
                self.send(400, {'error': 'invalid_payload'})
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    server = make_server(token=os.environ.get('SHARE4AI_PROVIDER_TOKEN', ''))
    print('Share4AI local protocol fixture: http://127.0.0.1:8000 (no jobs, no persistence)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
