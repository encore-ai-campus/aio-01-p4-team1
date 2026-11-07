#!/usr/bin/env python3
"""Read-only contract employee fixture for isolated C04 transport tests, never a live data-api."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path

EXPECTED = {'이준호':'영업팀', '박서연':'재무팀', '최유진':'인사팀', '한지훈':'개발팀', '김민지':'IT팀', '정우성':'IT팀'}


def create_server(key, rows, host, port):
    if not key or not isinstance(rows, list) or len(rows) != 6 or any(not isinstance(r, dict) or set(r) != {'name', 'dept'} for r in rows):
        raise ValueError('only the six contract name/department fixtures are allowed')
    if {r['name']: r['dept'] for r in rows} != EXPECTED:
        raise ValueError('contract employee mismatch')
    raw = json.dumps({'items': rows}, ensure_ascii=False).encode()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, status, body):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path != '/employees':
                return self.send(404, {'error': 'not_found'})
            if not hmac.compare_digest(self.headers.get('X-Api-Key', ''), key):
                return self.send(401, {'error': 'unauthorized'})
            self.send(200, raw)

        def do_POST(self):
            self.send(405, {'error': 'read_only_fixture'})

    return ThreadingHTTPServer((host, port), Handler)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixture', required=True)
    p.add_argument('--port', type=int, default=8802)
    args = p.parse_args()
    server = create_server(os.environ.get('INTERNAL_API_KEY', ''), json.loads(Path(args.fixture).read_text()), '0.0.0.0', args.port)
    print(json.dumps({'ready': True, 'scope': 'isolated contract fixture only'}), flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
