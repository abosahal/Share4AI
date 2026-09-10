"""Authenticated, loopback-only one-provider pilot. In-memory; never deploy publicly."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
import threading
import time
import uuid
from provider.jobs import sign_job, validate_messages, JobError


class Broker:
    def __init__(self, provider_token, clock=time.time):
        if not provider_token:
            raise ValueError('Provider token is required')
        self.token, self.clock = provider_token, clock
        self.condition = threading.Condition()
        self.node_id = None
        self.node = None
        self.jobs = {}

    def eligible(self, model=None):
        node = self.node
        return bool(node and self.clock() - node['seen'] < 20 and node.get('sharing_enabled') is True
                    and node.get('state') == 'AVAILABLE' and node.get('capabilities', {}).get('accepts_jobs') is True
                    and (model is None or node['capabilities'].get('model_sha256') == model))

    def terminal(self, item, kind, text=''):
        if not item['terminal']:
            item['events'].append({'kind': kind, 'text': text})
            item['terminal'] = True
            item['job']['messages'] = []  # Purge prompt once no longer needed.
            self.condition.notify_all()

    def expire(self):
        for item in self.jobs.values():
            if not item['terminal'] and (self.clock() >= item['job']['expires_at'] or
                    not self.node or self.clock() - self.node['seen'] >= 20):
                self.terminal(item, 'error', 'provider_offline_or_deadline')

    def register(self, payload, register=False):
        with self.condition:
            identity = payload.get('node_id')
            if not isinstance(identity, str) or not 1 <= len(identity) <= 100:
                return 400, {'error': 'invalid_node'}
            if self.node_id is not None and self.node_id != identity:
                return 403, {'error': 'credential_bound_to_other_node'}
            if not register and self.node is None:
                return 404, {'error': 'registration_required'}
            self.node_id = identity
            self.node = dict(payload, seen=self.clock())
            if payload.get('sharing_enabled') is not True:
                for item in self.jobs.values():
                    self.terminal(item, 'error', 'sharing_stopped')
            return 200, {'node_id': identity}

    def submit(self, messages, maximum, model):
        validate_messages(messages, maximum)
        if not isinstance(model, str) or len(model) != 64:
            raise JobError('Exact model SHA256 required')
        with self.condition:
            self.expire()
            if not self.eligible(model):
                raise JobError('No eligible provider for this model')
            if len(self.jobs) >= 32 or any(not item['terminal'] for item in self.jobs.values()):
                raise JobError('Provider busy; retry later')
            now = self.clock()
            job = dict(job_id=uuid.uuid4().hex, node_id=self.node_id, model_sha256=model,
                       issued_at=now, expires_at=now + 120, messages=messages, max_tokens=maximum)
            self.jobs[job['job_id']] = dict(job=job, signature=sign_job(job, self.token), claimed=False,
                events=[], terminal=False, sequence=0, bytes=0)
            return job['job_id']

    def provider_request(self, path, payload):
        with self.condition:
            self.expire()
            identity = payload.get('node_id')
            if self.node is None:
                return 404, {'error': 'registration_required'}
            if identity != self.node_id:
                return 403, {'error': 'wrong_node'}
            reply = {'node_id': identity}
            if path == '/v1/jobs/poll':
                envelope = None
                if self.eligible():
                    for item in self.jobs.values():
                        if not item['terminal'] and not item['claimed']:
                            item['claimed'] = True
                            # Copy through JSON: prompt erasure must not mutate already leased jobs.
                            envelope = json.loads(json.dumps({'job': item['job'], 'signature': item['signature']}))
                            break
                return 200, dict(reply, envelope=envelope)
            item = self.jobs.get(payload.get('job_id'))
            signature = payload.get('signature')
            if (not item or not item['claimed'] or not isinstance(signature, str)
                    or not hmac.compare_digest(signature, item['signature'])):
                return 403, {'error': 'invalid_job_authorization'}
            if path == '/v1/jobs/status':
                return 200, dict(reply, cancelled=item['terminal'])
            if path != '/v1/jobs/event':
                return 404, {'error': 'not_found'}
            if item['terminal']:
                return 409, {'error': 'job_closed'}
            if type(payload.get('sequence')) is not int or payload['sequence'] != item['sequence']:
                return 409, {'error': 'event_out_of_order'}
            kind, text = payload.get('kind'), payload.get('text', '')
            if kind not in ('token', 'done', 'error') or not isinstance(text, str) or len(text) > 16384:
                return 400, {'error': 'invalid_event'}
            if len(item['events']) >= 512 or item['bytes'] + len(text.encode()) > 262144:
                self.terminal(item, 'error', 'output_limit')
                return 413, {'error': 'output_limit'}
            item['sequence'] += 1
            item['bytes'] += len(text.encode())
            if kind == 'token':
                item['events'].append({'kind': kind, 'text': text})
                self.condition.notify_all()
            else:
                self.terminal(item, kind, 'provider_failed' if kind == 'error' else '')
            return 200, reply

    def next_events(self, identity, offset):
        with self.condition:
            self.expire()
            item = self.jobs[identity]
            if offset == len(item['events']) and not item['terminal']:
                self.condition.wait(0.5)
                self.expire()
            return list(item['events'][offset:]), item['terminal']

    def cancel(self, identity):
        with self.condition:
            item = self.jobs.get(identity)
            if item:
                self.terminal(item, 'error', 'client_disconnected')
                # Worker gets 403 and stops; no retention after consumer goes away.
                del self.jobs[identity]


def make_server(provider_token, client_token, port=8000):
    if not provider_token or not client_token or provider_token == client_token:
        raise ValueError('Two distinct nonempty credentials are required')
    broker = Broker(provider_token)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, value):
            data = json.dumps(value).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            self.connection.settimeout(5)
            is_chat = self.path == '/v1/chat/stream'
            expected = client_token if is_chat else provider_token
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 65536:
                    self.send(413, {'error': 'request_limit'}); return
                raw = self.rfile.read(length)
                if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + expected):
                    self.send(401, {'error': 'unauthorized'}); return
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError()
            except (ValueError, OSError):
                self.send(400, {'error': 'invalid_request'}); return
            if is_chat:
                try:
                    identity = broker.submit(payload.get('messages'), payload.get('max_tokens', 256), payload.get('model_sha256'))
                except JobError:
                    self.send(409, {'error': 'invalid_request_or_provider_unavailable'}); return
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    offset = 0
                    while True:
                        events, terminal = broker.next_events(identity, offset)
                        for event in events:
                            data = ('data: ' + json.dumps(event) + '\n\n').encode()
                            self.wfile.write(data)
                        offset += len(events)
                        if not events:
                            self.wfile.write(b': keepalive\n\n')
                        self.wfile.flush()
                        if terminal:
                            break
                except OSError:
                    pass
                finally:
                    broker.cancel(identity)
                return
            if self.path in ('/v1/nodes/register', '/v1/nodes/heartbeat'):
                code, result = broker.register(payload, self.path.endswith('/register'))
            else:
                code, result = broker.provider_request(self.path, payload)
            self.send(code, result)
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.broker = broker
    return server


if __name__ == '__main__':
    server = make_server(os.environ.get('SHARE4AI_PROVIDER_TOKEN', ''), os.environ.get('SHARE4AI_CLIENT_TOKEN', ''))
    print('Share4AI authenticated local pilot on 127.0.0.1:8000; one trusted provider; memory only')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
