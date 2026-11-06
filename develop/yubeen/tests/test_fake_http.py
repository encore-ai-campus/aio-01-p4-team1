"""Fake servers over loopback; all external providers remain unused."""
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
import fake_http
import index_http
import search_http


class FakeHttpTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'SEARCH_TEAM_KEY': 'fake-search-key',
                                         'INDEX_TEAM_KEY': 'fake-index-key'}, clear=True)
        self.env.start()
        self.search = ThreadingHTTPServer(('127.0.0.1', 0), search_http.make_handler(fake_http.fake_search))
        self.index = ThreadingHTTPServer(('127.0.0.1', 0),
            index_http.make_handler(lambda *a, **k: fake_http.fake_index(*a, **k)))
        self.threads = []
        for server in (self.search, self.index):
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.threads.append(thread)

    def tearDown(self):
        for server, thread in zip((self.search, self.index), self.threads):
            server.shutdown()
            server.server_close()
            thread.join()
        self.env.stop()

    def send(self, server, path, body=b'', key=None):
        headers = {'Content-Type': 'application/json'}
        if key is not None:
            headers['X-Team-Key'] = key
        req = Request(f'http://127.0.0.1:{server.server_port}{path}', data=body,
                      headers=headers, method='POST')
        try:
            response = urlopen(req, timeout=2)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response)

    def search_body(self, **changes):
        body = {'request_id': 'fake-1', 'query': '합성 질문', 'type': 'test',
                'access_levels': ['all'], 'top_k': 3}
        body.update(changes)
        return json.dumps(body).encode()

    def test_search_contract_all_statuses(self):
        path = '/webhook/oke-search'
        self.assertEqual(self.send(self.search, path, self.search_body(), 'fake-search-key')[0], 200)
        status, body = self.send(self.search, path, self.search_body(query='__fake_empty__'), 'fake-search-key')
        self.assertEqual((status, body['evidence'], body['reason']), (200, [], 'no_evidence'))
        self.assertEqual(self.send(self.search, path, self.search_body(query='__fake_503__'), 'fake-search-key')[0], 503)
        self.assertEqual(self.send(self.search, path, self.search_body(), None)[0], 401)
        self.assertEqual(self.send(self.search, path, self.search_body(), 'wrong')[0], 401)
        self.assertEqual(self.send(self.search, path, self.search_body(top_k=4), 'fake-search-key')[0], 400)
        self.assertEqual(self.send(self.search, path, self.search_body(access_levels=['all','it']), 'fake-search-key')[0], 200)
        self.assertEqual(self.send(self.search, path, self.search_body(access_levels=['it']), 'fake-search-key')[0], 400)

    def test_index_success_auth_input_and_failure(self):
        path = '/internal/oke-index'
        status, body = self.send(self.index, path, key='fake-index-key')
        self.assertEqual((status, body['mode'], len(body['documents'])), (200, 'mock', 8))
        self.assertEqual(self.send(self.index, path)[0], 401)
        self.assertEqual(self.send(self.index, path, key='wrong')[0], 401)
        self.assertEqual(self.send(self.index, path, body=b'{}', key='fake-index-key')[0], 400)
        self.assertEqual(fake_http.fake_index(outcome='success')['counts']['indexed'], 8)
        with self.assertRaises(RuntimeError):
            fake_http.fake_index(outcome='unavailable')

    def test_index_503_is_sanitized(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), index_http.make_handler(
            lambda *a, **k: fake_http.fake_index(*a, outcome='unavailable', **k)))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status, body = self.send(server, '/internal/oke-index', key='fake-index-key')
            self.assertEqual((status, body), (503, {'ok': False, 'reason': 'index_unavailable'}))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
