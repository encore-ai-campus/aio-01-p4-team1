"""Internal, authenticated trigger for server-owned RAG indexing configuration."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading

import rag_load

_lock = threading.Lock()


def make_handler(run=rag_load.execute):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, body):
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path != '/internal/oke-index':
                return self.reply(404, {'ok': False, 'reason': 'not_found'})
            key = os.environ.get('INDEX_TEAM_KEY', '')
            if not key or not hmac.compare_digest(self.headers.get('X-Team-Key', '').encode('utf-8'), key.encode('utf-8')):
                return self.reply(401, {'ok': False, 'reason': 'unauthorized'})
            if self.headers.get('Content-Length', '0') != '0':
                return self.reply(400, {'ok': False, 'reason': 'invalid_request'})
            if not _lock.acquire(blocking=False):
                return self.reply(409, {'ok': False, 'reason': 'index_in_progress'})
            try:
                try:
                    result = run(os.environ.get('RAG_DOCS_DIR', ''), os.environ.get('RAG_PERMISSIONS_FILE', ''),
                                 mode='real', allow_external=True)
                    return self.reply(200 if result['ok'] else 503, result)
                except Exception:
                    return self.reply(503, {'ok': False, 'reason': 'index_unavailable'})
            finally:
                _lock.release()
    return Handler


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=os.environ.get('INDEX_HOST', '127.0.0.1'))
    parser.add_argument('--port', type=int, default=int(os.environ.get('INDEX_PORT', '8766')))
    args = parser.parse_args()
    for key in ('INDEX_TEAM_KEY', 'RAG_DOCS_DIR', 'RAG_PERMISSIONS_FILE', 'DATABASE_URL', 'OPENAI_API_KEY'):
        if not os.environ.get(key):
            parser.error(key + ' is required')
    with ThreadingHTTPServer((args.host, args.port), make_handler()) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
