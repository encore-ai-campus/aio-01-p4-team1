"""Standalone C03 HTTP entry point for authenticated support requests."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os

from rag_search import OpenAIEmbeddingProvider, PgvectorSearchAdapter, search_with_adapters, unavailable, valid_levels


def validate_request(body):
    if not isinstance(body, dict):
        return False
    return (isinstance(body.get('request_id'), str) and 1 <= len(body['request_id']) <= 64
            and isinstance(body.get('query'), str) and bool(body['query'].strip())
            and isinstance(body.get('type'), str) and bool(body['type'].strip())
            and valid_levels(body.get('access_levels')) and type(body.get('top_k')) is int
            and body['top_k'] == 3)


def live_search(body):
    if not validate_request(body):
        return unavailable()
    dsn = os.environ.get('DATABASE_URL')
    if not dsn or not os.environ.get('OPENAI_API_KEY'):
        return unavailable()
    try:
        import psycopg  # Optional until the DB is ready.
        with psycopg.connect(dsn, connect_timeout=3,
                             options='-c statement_timeout=3000 -c default_transaction_read_only=on',
                             autocommit=True) as connection:
            return search_with_adapters(body['query'], body['access_levels'], 3,
                                        OpenAIEmbeddingProvider(timeout=3),
                                        PgvectorSearchAdapter(connection))
    except Exception:
        return unavailable()


def make_handler(search=live_search):
    """Accept the support-owned access list only after X-Team-Key authentication."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Never log URLs, credentials, or question text.

        def send_json(self, status, body):
            data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path != '/webhook/oke-search':
                return self.send_json(404, {'ok': False, 'evidence': [], 'reason': 'not_found'})
            key = os.environ.get('SEARCH_TEAM_KEY', '')
            supplied = self.headers.get('X-Team-Key', '')
            if not key or not hmac.compare_digest(supplied, key):
                return self.send_json(401, {'ok': False, 'evidence': [], 'reason': 'unauthorized'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length < 1 or length > 65536:
                    raise ValueError()
                body = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                return self.send_json(400, {'ok': False, 'evidence': [], 'reason': 'invalid_request'})
            if not validate_request(body):
                return self.send_json(400, {'ok': False, 'evidence': [], 'reason': 'invalid_request'})
            try:
                status, result = search(body)
                if status not in (200, 503):
                    raise ValueError()
            except Exception:
                status, result = unavailable()
            self.send_json(status, result)
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=os.environ.get('SEARCH_HOST', '127.0.0.1'))
    parser.add_argument('--port', type=int, default=int(os.environ.get('SEARCH_PORT', '8765')))
    args = parser.parse_args()
    if not os.environ.get('SEARCH_TEAM_KEY'):
        parser.error('SEARCH_TEAM_KEY is required')
    if os.environ.get('SEARCH_MODE', 'live') != 'live':
        parser.error('SEARCH_MODE must be live')
    with ThreadingHTTPServer((args.host, args.port), make_handler()) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
