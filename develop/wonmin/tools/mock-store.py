#!/usr/bin/env python3
"""Ephemeral C05 HTTP test store. Not a backend, data-api or PostgreSQL replacement."""
import argparse
import hashlib
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

EMPLOYEES = {'이준호', '박서연', '최유진', '한지훈', '김민지', '정우성'}


class MockServer(ThreadingHTTPServer):
    # Keep concurrent test connections from queuing behind platform TCP backlog defaults.
    request_queue_size = 64


class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.tickets = {}
        self.alerts = []
        self.events = {}
        self.calls = {'tickets': 0, 'alerts': 0}

    def ticket(self, body):
        fields = ('key', 'title', 'requester', 'category', 'priority')
        if (not all(isinstance(body.get(f), str) and body[f].strip() for f in fields)
                or len(body['key']) > 64 or body['priority'] not in {'normal', 'high'}
                or body['requester'] not in EMPLOYEES):
            return 400, {'error': 'invalid_input'}
        payload = {f: body[f] for f in fields}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        key_hash = hashlib.sha256(body['key'].encode()).hexdigest()
        with self.lock:
            self.calls['tickets'] += 1
            existing = self.tickets.get(key_hash)
            if existing:
                if existing['payload_hash'] != digest:
                    return 409, {'error': 'request_conflict'}
                return 200, {'ticket_id': existing['ticket_id'], 'duplicate': True}
            ticket_id = f'T-{2001 + len(self.tickets)}'
            self.tickets[key_hash] = {'ticket_id': ticket_id, 'key_hash': key_hash,
                                      'payload_hash': digest, 'priority': body['priority']}
            return 201, {'ticket_id': ticket_id, 'duplicate': False}

    def alert(self, body):
        if (not all(isinstance(body.get(f), str) and body[f].strip()
                    for f in ('workflow', 'node', 'message', 'severity'))
                or any(f in body and (not isinstance(body[f], str) or not body[f].strip())
                       for f in ('ticket_id', 'event_key'))):
            return 400, {'error': 'invalid_input'}
        # Retain only safe observation fields; never store incoming message/body/credentials.
        event = body.get('event_key')
        event_hash = hashlib.sha256(event.encode()).hexdigest() if event else None
        with self.lock:
            self.calls['alerts'] += 1
            if event_hash and event_hash in self.events:
                return 200, {'stored': 0, 'count': len(self.alerts), 'duplicate': True}
            self.alerts.append({'ticket_id': body.get('ticket_id'), 'severity': body['severity']})
            if event_hash:
                self.events[event_hash] = True
            return 200, {'stored': 1, 'count': len(self.alerts)}

    def snapshot(self):
        with self.lock:
            return {'mock': True, 'ephemeral': True, 'ticket_count': len(self.tickets),
                    'alert_count': len(self.alerts), 'calls': dict(self.calls),
                    'tickets': [{k: v for k, v in t.items() if k != 'payload_hash'}
                                for t in self.tickets.values()], 'alerts': list(self.alerts)}


def handler(store, secret):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No URL, body, contact, credential or stack output.

        def reply(self, status, body):
            encoded = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def authorized(self):
            supplied = self.headers.get('X-Api-Key', '').encode()
            if not hmac.compare_digest(supplied, secret.encode()):
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
            if self.path not in {'/tickets', '/alerts'}:
                return self.reply(404, {'error': 'not_found'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if size < 1 or size > 16384:
                    return self.reply(400, {'error': 'invalid_input'})
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    return self.reply(400, {'error': 'invalid_input'})
            except (ValueError, UnicodeError):
                return self.reply(400, {'error': 'invalid_input'})
            status, response = store.ticket(body) if self.path == '/tickets' else store.alert(body)
            self.reply(status, response)

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1', help='Default: loopback. Container tests may explicitly bind 0.0.0.0.')
    parser.add_argument('--port', type=int, default=18800, help='Default: 18800; 0 selects a free local port.')
    args = parser.parse_args()
    secret = os.environ.get('INTERNAL_API_KEY', '')
    if not secret.strip():
        parser.error('INTERNAL_API_KEY must be set; its value is never printed')
    server = MockServer((args.host, args.port), handler(Store(), secret))
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
