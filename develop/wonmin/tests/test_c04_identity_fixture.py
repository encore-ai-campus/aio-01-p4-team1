"""Actual HTTP boundary tests for the explicitly synthetic employee provider."""
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

SOURCE = Path(__file__).resolve().parents[1] / 'tools/c04-identity-fixture.py'


class IdentityFixtureTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SOURCE.exists(), 'read-only identity fixture must exist')
        spec = importlib.util.spec_from_file_location('identity_fixture', SOURCE)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.rows = [{'name': n, 'dept': d} for n, d in [('이준호','영업팀'),('박서연','재무팀'),('최유진','인사팀'),('한지훈','개발팀'),('김민지','IT팀'),('정우성','IT팀')]]
        self.server = self.module.create_server('synthetic-test-key', self.rows, '127.0.0.1', 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, path, key='synthetic-test-key', method='GET'):
        req = Request('http://127.0.0.1:' + str(self.server.server_port) + path,
                      headers={'X-Api-Key': key}, method=method)
        try:
            with urlopen(req) as reply:
                return reply.status, json.load(reply)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_contract_employees_are_read_only_and_unknown_routes_reject(self):
        status, body = self.request('/employees')
        self.assertEqual(status, 200)
        self.assertEqual(body, {'items': self.rows})
        self.assertEqual(self.request('/employees', method='POST')[0], 405)
        self.assertEqual(self.request('/employees?requester=any')[0], 404)
        self.assertEqual(self.request('/tickets')[0], 404)
        self.assertEqual(self.request('/employees')[1], body)

    def test_missing_or_wrong_auth_never_exposes_employees(self):
        for key in ('', 'wrong'):
            status, body = self.request('/employees', key)
            self.assertEqual(status, 401)
            self.assertNotIn('items', body)

    def test_unexpected_fixture_data_fails_closed(self):
        for rows in ([], self.rows + [self.rows[0]], [{**r, 'phone': 'synthetic-private'} for r in self.rows]):
            with self.assertRaises(ValueError):
                self.module.create_server('synthetic-test-key', rows, '127.0.0.1', 0)


if __name__ == '__main__':
    unittest.main()
