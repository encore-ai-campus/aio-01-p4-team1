#!/usr/bin/env python3
"""Private lab fault injector; normal requests always reach the real C05 backend."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ENDPOINTS = ('tickets', 'alerts', 'dlq')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8801)
    args = parser.parse_args()
    key = os.environ.get('INTERNAL_API_KEY', '')
    base = os.environ.get('WONMIN_C05_UPSTREAM', '').rstrip('/')
    target = urlsplit(base)
    if not key or target.scheme not in ('http', 'https') or not target.hostname or target.username or target.password or target.path or target.query or target.fragment:
        parser.error('private upstream origin and key must be configured')
    plan = json.loads(os.environ.get('WONMIN_C05_FAULTS', '{}'))
    if not isinstance(plan, dict) or any(k not in ENDPOINTS or not isinstance(v, list) or not v
            or any(type(s) is not int or s not in (0, 429, 500, 503) for s in v) for k, v in plan.items()):
        parser.error('fault plan must contain endpoint lists of 0/429/500/503')
    lock = threading.Lock()
    calls, forwarded, forced = ({k: 0 for k in ENDPOINTS} for _ in range(3))
    opener = build_opener(NoRedirect())

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, status, data):
            raw = data if isinstance(data, bytes) else json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def authorized(self):
            if hmac.compare_digest(self.headers.get('X-Api-Key', ''), key):
                return True
            self.send(401, {'error': 'unauthorized'})
            return False

        def do_GET(self):
            if self.path != '/_lab/ops':
                return self.send(404, {'error': 'not_found'})
            if self.authorized():
                with lock:
                    self.send(200, {'scope': 'fault injector forwarding to real FastAPI',
                                    'calls': dict(calls), 'forwarded': dict(forwarded), 'forced': dict(forced)})

        def do_POST(self):
            endpoint = self.path.removeprefix('/')
            if endpoint not in ENDPOINTS or self.path != '/' + endpoint:
                return self.send(404, {'error': 'not_found'})
            if not self.authorized():
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 65536:
                    raise ValueError()
                raw = self.rfile.read(size)
            except ValueError:
                return self.send(400, {'error': 'invalid_request'})
            with lock:
                index = calls[endpoint]
                calls[endpoint] += 1
                sequence = plan.get(endpoint, [0])
                status = sequence[min(index, len(sequence) - 1)]
                if status:
                    forced[endpoint] += 1
                else:
                    forwarded[endpoint] += 1
            if status:
                return self.send(status, {'error': 'lab_injected_fault'})
            request = Request(base + '/' + endpoint, data=raw, method='POST',
                              headers={'Content-Type': 'application/json', 'X-Api-Key': key})
            try:
                with opener.open(request, timeout=3) as response:
                    self.send(response.status, response.read(1048576))
            except HTTPError as error:
                with error:
                    self.send(error.code, error.read(1048576))
            except (URLError, OSError):
                self.send(503, {'error': 'upstream_unavailable'})

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(json.dumps({'ready': True, 'port': server.server_port}), flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
