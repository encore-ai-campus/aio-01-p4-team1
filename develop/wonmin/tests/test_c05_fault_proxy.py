"""Real HTTP tests for controlled failure injection in front of an upstream service."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/c05-fault-proxy.py'
KEY = 'synthetic-proxy-test-key'


class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.received = []
        received = self.received

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers['Content-Length']))
                received.append((self.path, dict(self.headers), raw))
                data = json.dumps({'stored': 1, 'sha256': hashlib.sha256(raw).hexdigest()}).encode()
                self.send_response(201)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        self.thread = threading.Thread(target=self.upstream.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.upstream.server_close)
        self.addCleanup(self.upstream.shutdown)

    def start_proxy(self, plan):
        env = {**os.environ, 'INTERNAL_API_KEY': KEY,
               'WONMIN_C05_UPSTREAM': f'http://127.0.0.1:{self.upstream.server_port}',
               'WONMIN_C05_FAULTS': json.dumps(plan)}
        child = subprocess.Popen(['python3', '-B', str(SCRIPT), '--port', '0'], env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        def stop():
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=5)
            child.stdout.close(); child.stderr.close()
        self.addCleanup(stop)
        lines = queue.Queue()
        threading.Thread(target=lambda: lines.put(child.stdout.readline()), daemon=True).start()
        line = lines.get(timeout=5)
        self.assertTrue(line, 'proxy did not announce HTTP readiness')
        self.base = 'http://127.0.0.1:' + str(json.loads(line)['port'])

    def call(self, path, key=KEY, body=b'{"example":"private synthetic input"}', method='POST', extra=None):
        req = Request(self.base + path, data=body if method == 'POST' else None, method=method,
                      headers={'Content-Type': 'application/json', 'X-Api-Key': key, **(extra or {})})
        try:
            with urlopen(req, timeout=3) as r:
                return r.status, json.load(r)
        except HTTPError as r:
            with r:
                return r.code, json.load(r)

    def test_normal_forwards_exact_body_and_status_without_browser_credentials(self):
        self.start_proxy({})
        status, reply = self.call('/tickets', extra={'Cookie': 'synthetic-session', 'Authorization': 'Bearer synthetic'})
        self.assertEqual(status, 201)
        self.assertEqual(reply['sha256'], hashlib.sha256(self.received[0][2]).hexdigest())
        headers = {k.lower(): v for k, v in self.received[0][1].items()}
        self.assertEqual(headers['x-api-key'], KEY)
        self.assertNotIn('cookie', headers)
        self.assertNotIn('authorization', headers)

    def test_wrong_key_rejects_without_contacting_upstream(self):
        self.start_proxy({})
        self.assertEqual(self.call('/tickets', key='invalid')[0], 401)
        self.assertEqual(self.received, [])

    def test_alert_failure_does_not_block_other_real_endpoints(self):
        self.start_proxy({'alerts': [503]})
        self.assertEqual(self.call('/alerts')[0], 503)
        self.assertEqual(self.call('/dlq')[0], 201)
        self.assertEqual([r[0] for r in self.received], ['/dlq'])

    def test_transient_ticket_failure_forwards_the_second_attempt(self):
        self.start_proxy({'tickets': [503, 0]})
        self.assertEqual(self.call('/tickets')[0], 503)
        self.assertEqual(self.call('/tickets')[0], 201)
        self.assertEqual(len(self.received), 1)

    def test_observations_are_read_only_counts_without_payload_or_key(self):
        self.start_proxy({})
        self.call('/alerts')
        status, ops = self.call('/_lab/ops', method='GET')
        self.assertEqual(status, 200)
        self.assertEqual(ops['calls']['alerts'], 1)
        self.assertEqual(ops['forwarded']['alerts'], 1)
        self.assertNotIn(KEY, json.dumps(ops))
        self.assertNotIn('private synthetic input', json.dumps(ops))
        self.assertEqual(self.call('/_lab/reset')[0], 404)
        self.assertEqual(len(self.received), 1)


if __name__ == '__main__':
    unittest.main()
