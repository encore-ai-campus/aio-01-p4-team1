"""Local Fake HTTP only; real index runner is injected out."""
import json
import os
from pathlib import Path
import sys
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import index_http


class IndexHttpTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def fake_run(*args, **kwargs):
            self.calls.append((args, kwargs))
            return {'ok': True, 'mode': 'mock', 'counts': {'indexed': 8, 'skipped': 0, 'rejected': 0, 'failed': 0},
                    'documents': [{'doc_key': str(i), 'status': 'indexed', 'chunk_count': 1, 'reason': None} for i in range(8)]}
        self.env = patch.dict(os.environ, {'INDEX_TEAM_KEY': 'fake-key', 'RAG_DOCS_DIR': 'fake-docs',
                                         'RAG_PERMISSIONS_FILE': 'fake-permissions'}, clear=True)
        self.env.start()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), index_http.make_handler(fake_run))
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.env.stop()

    def send(self, key=None, body=b''):
        headers = {'Content-Length': str(len(body))}
        if key is not None:
            headers['X-Team-Key'] = key
        request = Request(f'http://127.0.0.1:{self.server.server_port}/internal/oke-index',
                          data=body, headers=headers, method='POST')
        try:
            response = urlopen(request, timeout=2)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response)

    def test_auth_and_body_rejected_before_runner(self):
        self.assertEqual(self.send()[0], 401)
        self.assertEqual(self.send('wrong')[0], 401)
        self.assertEqual(self.send('fake-key', b'{}')[0], 400)
        self.assertEqual(self.calls, [])

    def test_authenticated_trigger_uses_server_paths(self):
        status, body = self.send('fake-key')
        self.assertEqual(status, 200)
        self.assertTrue(body['ok'])
        self.assertEqual(self.calls, [(('fake-docs', 'fake-permissions'), {'mode': 'real', 'allow_external': True})])


if __name__ == '__main__':
    unittest.main()
