"""FAKE adapter over a real local HTTP socket; no DB or OpenAI call."""
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
import search_http


class SearchHttpTests(unittest.TestCase):
    def setUp(self):
        self.fake_calls = []
        def fake_search(body):
            self.fake_calls.append(body)
            if body['query'] == 'fault':
                raise RuntimeError('private DB password')
            rows = [] if body['query'] == 'empty' else [
                {'doc': 'public', 'section': 's', 'text': 'safe', 'score': 0.7}]
            if body['access_levels'] == ['all', 'it']:
                rows.append({'doc': 'restricted', 'section': 's', 'text': 'it', 'score': 0.6})
            return 200, {'ok': True, 'evidence': rows,
                         'reason': None if rows else 'no_evidence'}
        self.env = patch.dict(os.environ, {'SEARCH_TEAM_KEY': 'fake-test-only'}, clear=True)
        self.env.start()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), search_http.make_handler(fake_search))
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.env.stop()

    def send(self, body, key='fake-test-only'):
        request = Request(f'http://127.0.0.1:{self.server.server_port}/webhook/oke-search',
                          data=json.dumps(body).encode(), method='POST',
                          headers={'X-Team-Key': key, 'Content-Type': 'application/json'})
        try:
            response = urlopen(request, timeout=2)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def body(self, **changes):
        body = dict(request_id='fake-001', query='vpn', type='network',
                    access_levels=['all'], top_k=3)
        body.update(changes)
        return body

    def test_fake_http_success_empty_fault(self):
        self.assertEqual(self.send(self.body())[0], 200)
        self.assertEqual(self.send(self.body(query='empty'))[1]['reason'], 'no_evidence')
        self.assertEqual(self.send(self.body(query='fault')),
                         (503, {'ok': False, 'evidence': [], 'reason': 'search_unavailable'}))

    def test_auth_input_and_it_spoof(self):
        self.assertEqual(self.send(self.body(), key='wrong')[0], 401)
        self.assertEqual(self.send(self.body(query=''))[0], 400)
        self.assertEqual(self.send(self.body(access_levels=['all', 'it'], role='admin'))[0], 200)
        self.assertEqual(self.send(self.body(is_admin=True, access_levels=['it']))[0], 400)
        self.assertEqual(len(self.fake_calls), 1)

    def test_missing_key_and_invalid_levels(self):
        self.assertEqual(self.send(self.body(), key='')[0], 401)
        for levels in ([], ['it'], ['all', 'unknown'], 'all'):
            self.assertEqual(self.send(self.body(access_levels=levels))[0], 400)
        self.assertEqual(self.fake_calls, [])

    def test_authenticated_levels_filter_evidence(self):
        status, result = self.send(self.body())
        self.assertEqual(status, 200)
        self.assertEqual([row['doc'] for row in result['evidence']], ['public'])
        status, result = self.send(self.body(access_levels=['all', 'it']))
        self.assertEqual(status, 200)
        self.assertEqual([row['doc'] for row in result['evidence']], ['public', 'restricted'])
        calls = len(self.fake_calls)
        self.assertEqual(self.send(self.body(access_levels=['all', 'it']), key='wrong')[0], 401)
        self.assertEqual(len(self.fake_calls), calls)

    def test_missing_live_config_is_unavailable(self):
        self.assertEqual(search_http.live_search(self.body()), search_http.unavailable())


if __name__ == '__main__':
    unittest.main()
