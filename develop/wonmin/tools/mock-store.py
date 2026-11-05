#!/usr/bin/env python3
"""Ephemeral C05 HTTP test store with environment-only fault plans; not a backend."""
import argparse
import hashlib
import hmac
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

EMPLOYEES = {'이준호', '박서연', '최유진', '한지훈', '김민지', '정우성'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def valid(endpoint, body):
    if endpoint == 'tickets':
        return (all(nonempty(body.get(f)) for f in ('key', 'title', 'requester', 'category', 'priority'))
                and len(body['key']) <= 64 and body['requester'] in EMPLOYEES
                and body['priority'] in {'normal', 'high'})
    if endpoint == 'alerts':
        return (all(nonempty(body.get(f)) for f in ('workflow', 'node', 'message', 'severity'))
                and all(f not in body or body[f] is None or nonempty(body[f]) for f in ('ticket_id', 'event_key')))
    return ('request_id' in body and (body['request_id'] is None
            or (nonempty(body['request_id']) and len(body['request_id']) <= 64))
            and all(nonempty(body.get(f)) for f in ('workflow', 'node', 'reason'))
            and isinstance(body.get('safe_payload'), dict)
            and (body.get('execution_ref') is None or nonempty(body['execution_ref'])))


class MockServer(ThreadingHTTPServer):
    request_queue_size = 64


class Store:
    def __init__(self, faults):
        self.lock = threading.Lock()
        self.tickets = {}
        self.alerts = []
        self.dlqs = []
        self.events = set()
        self.calls = {name: 0 for name in ('tickets', 'alerts', 'dlq')}
        self.attempts = []
        self.faults = faults

    def begin(self, endpoint, body):
        with self.lock:
            index = self.calls[endpoint]
            self.calls[endpoint] += 1
            self.attempts.append({'endpoint': endpoint, 'payload_hash': digest(body),
                                  'key_hash': digest(body.get('key')) if endpoint == 'tickets' else None})
            plan = self.faults.get(endpoint, [{}])
            return plan[min(index, len(plan) - 1)]

    def ticket(self, body):
        payload = {f: body[f] for f in ('key', 'title', 'requester', 'category', 'priority')}
        payload_hash, key_hash = digest(payload), digest(body['key'])
        with self.lock:
            existing = self.tickets.get(key_hash)
            if existing:
                if existing['payload_hash'] != payload_hash:
                    return 409, {'error': 'request_conflict'}
                return 200, {'ticket_id': existing['ticket_id'], 'duplicate': True}
            ticket_id = f'T-{2001 + len(self.tickets)}'
            self.tickets[key_hash] = {'ticket_id': ticket_id, 'key_hash': key_hash,
                                      'payload_hash': payload_hash, 'priority': body['priority']}
            return 201, {'ticket_id': ticket_id, 'duplicate': False}

    def alert(self, body):
        event_hash = digest(body['event_key']) if body.get('event_key') else None
        with self.lock:
            if event_hash and event_hash in self.events:
                return 200, {'stored': 0, 'count': len(self.alerts), 'duplicate': True}
            self.alerts.append({'ticket_id': body.get('ticket_id'), 'severity': body['severity']})
            if event_hash:
                self.events.add(event_hash)
            return 200, {'stored': 1, 'count': len(self.alerts), 'duplicate': False}

    def dlq(self, body):
        # Keep only safe operational fields. Not a raw-payload store or automatic replay queue.
        original = body['safe_payload']
        safe = {}
        if isinstance(original.get('stage'), str) and original['stage'] in {'ticket', 'alert'}:
            safe['stage'] = original['stage']
        if isinstance(original.get('priority'), str) and original['priority'] in {'normal', 'high'}:
            safe['priority'] = original['priority']
        for field in ('attempts', 'last_status'):
            if type(original.get(field)) is int:
                safe[field] = original[field]
        ticket_id = original.get('ticket_id')
        if isinstance(ticket_id, str) and ticket_id.startswith('T-') and ticket_id[2:].isdigit():
            safe['ticket_id'] = ticket_id
        with self.lock:
            self.dlqs.append({'request_id_hash': digest(body['request_id']), 'safe_payload': safe})
            return 200, {'stored': 1, 'count': len(self.dlqs)}

    def snapshot(self):
        with self.lock:
            return {'mock': True, 'ephemeral': True, 'ticket_count': len(self.tickets),
                    'alert_count': len(self.alerts), 'dlq_count': len(self.dlqs), 'calls': dict(self.calls),
                    'tickets': [{k: v for k, v in t.items() if k != 'payload_hash'} for t in self.tickets.values()],
                    'alerts': list(self.alerts), 'dlqs': list(self.dlqs), 'attempts': list(self.attempts)}


def handler(store, secret):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body, retry_after=None):
            encoded = json.dumps(body, ensure_ascii=False).encode()
            try:
                self.send_response(status)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(encoded)))
                if retry_after is not None:
                    self.send_header('Retry-After', retry_after)
                self.end_headers()
                self.wfile.write(encoded)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Expected after a client timeout; do not log request data or stack.

        def authorized(self):
            if not hmac.compare_digest(self.headers.get('X-Api-Key', '').encode(), secret.encode()):
                self.reply(401, {'error': 'unauthorized'})
                return False
            return True

        def do_GET(self):
            if not self.authorized():
                return
            if self.path != '/_mock/ops':
                return self.reply(404, {'error': 'not_found'})
            self.reply(200, store.snapshot())

        def do_POST(self):
            if not self.authorized():
                return
            if self.path not in {'/tickets', '/alerts', '/dlq'}:
                return self.reply(404, {'error': 'not_found'})
            endpoint = self.path[1:]
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if size < 1 or size > 16384:
                    return self.reply(400, {'error': 'invalid_input'})
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict) or not valid(endpoint, body):
                    return self.reply(400, {'error': 'invalid_input'})
            except (ValueError, UnicodeError):
                return self.reply(400, {'error': 'invalid_input'})
            step = store.begin(endpoint, body)
            time.sleep(step.get('delay_ms', 0) / 1000)
            status = step.get('status', 200)
            if status >= 400:
                return self.reply(status, {'error': 'mock_fault'}, step.get('retry_after'))
            status, response = getattr(store, 'ticket' if endpoint == 'tickets' else 'alert' if endpoint == 'alerts' else 'dlq')(body)
            self.reply(status, response)

    return Handler


def load_faults():
    faults = json.loads(os.environ.get('WONMIN_MOCK_FAULTS', '{}'))
    if not isinstance(faults, dict) or any(name not in {'tickets', 'alerts', 'dlq'} for name in faults):
        raise ValueError('invalid fault plan')
    for plan in faults.values():
        if not isinstance(plan, list) or not plan:
            raise ValueError('invalid fault plan')
        for step in plan:
            if not isinstance(step, dict) or set(step) - {'status', 'delay_ms', 'retry_after'}:
                raise ValueError('invalid fault plan')
            if type(step.get('status', 200)) is not int or not 200 <= step.get('status', 200) <= 599:
                raise ValueError('invalid fault status')
            if type(step.get('delay_ms', 0)) is not int or not 0 <= step.get('delay_ms', 0) <= 10000:
                raise ValueError('invalid fault delay')
            value = step.get('retry_after', '')
            if not isinstance(value, str) or len(value) > 100 or '\r' in value or '\n' in value:
                raise ValueError('invalid retry-after')
    return faults


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='WONMIN_MOCK_FAULTS: JSON endpoint -> list of {status, delay_ms, retry_after}. Last step repeats. No reset/fault API.')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=18800, help='0 selects an unused local port')
    args = parser.parse_args()
    secret = os.environ.get('INTERNAL_API_KEY', '')
    if not secret.strip():
        parser.error('INTERNAL_API_KEY must be set; its value is never printed')
    try:
        store = Store(load_faults())
    except (ValueError, TypeError):
        parser.error('WONMIN_MOCK_FAULTS is invalid; its value is not printed')
    server = MockServer((args.host, args.port), handler(store, secret))
    server.daemon_threads = True
    print(json.dumps({'mock': True, 'host': args.host, 'port': server.server_port}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
