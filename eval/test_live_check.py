"""Regression checks for authentication, strict verdicts and private report contents."""
import copy
import http.server
import json
import threading
import unittest
from unittest.mock import patch

from live_check import (Session, assess_db, assess_normal, measure_response, run_checks, validate_origin)


class FixtureAPI(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body, cookie=None):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        if cookie:
            self.send_header('Set-Cookie', 'fixture_session=' + cookie + '; HttpOnly; Path=/')
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode())

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path == '/api/auth/login':
            role = 'admin' if data['login_id'] == 'fixture-admin' else 'employee'
            self.reply(200, {'user': {'must_change_password': False}}, role)
        elif self.path == '/api/auth/logout':
            self.reply(200, {'ok': True})
        elif self.path == '/api/ask':
            self.server.request_ids.append(data['request_id'])
            if data['attempt'] == 3:
                duplicate = data['request_id'] in self.server.seen
                self.server.seen.add(data['request_id'])
                self.server.rid = data['request_id']
                self.reply(200, {'route': '담당자 이관', 'sources': [], 'ticket': {
                    'ticket_id': 'T-fixture', 'duplicate': duplicate}, 'answer': 'PRIVATE_BODY_SENTINEL'})
            else:
                self.reply(200, {'route': '자동 답변', 'ticket': None,
                    'sources': [{'doc': self.server.doc}], 'answer': 'PRIVATE_BODY_SENTINEL'})
        else:
            self.reply(404, {})

    def do_GET(self):
        if self.path == '/api/my-requests':
            self.reply(200, {'items': [{'request_id': self.server.rid,
                'ticket': {'ticket_id': 'T-fixture'}, 'question': 'PRIVATE_BODY_SENTINEL'}]})
        elif self.path == '/api/admin/tickets':
            if 'fixture_session=admin' not in self.headers.get('Cookie', ''):
                self.reply(403, {})
            else:
                self.reply(200, {'items': [{'request_id': self.server.rid,
                    'ticket_id': 'T-fixture', 'requester': 'PRIVATE_BODY_SENTINEL'}]})
        elif self.path == '/api/admin/alerts':
            self.reply(200, {'items': self.server.alerts})
        elif self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/must-not-be-followed')
            self.end_headers()
        else:
            self.server.unexpected_requests += 1
            self.reply(200, {})


class LiveChecksTests(unittest.TestCase):
    def setUp(self):
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), FixtureAPI)
        self.server.seen = set()
        self.server.rid = None
        self.server.request_ids = []
        self.server.doc = 'password-policy'
        self.server.alerts = [{'ticket_id': 'T-fixture', 'message': 'PRIVATE_BODY_SENTINEL'}]
        self.server.unexpected_requests = 0
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f'http://127.0.0.1:{self.server.server_port}'
        self.settings = {'OKE_EMP_USER': 'fixture-employee', 'OKE_EMP_PASS': 'PRIVATE_PASSWORD_SENTINEL',
            'OKE_ADMIN_USER': 'fixture-admin', 'OKE_ADMIN_PASS': 'PRIVATE_ADMIN_SENTINEL'}
        self.receipt = {'inquiries': 1, 'tickets': 1, 'alerts': 1, 'completed': 1,
            'linked': 1, 'response_match': 1, 'ticket_ids': ['T-fixture'], 'dlq': 0}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_api_success_is_partial_without_direct_database_receipt(self):
        report = run_checks(self.origin, self.settings, normal_repeats=2)
        self.assertEqual(report['verdict'], 'PARTIAL_NO_DB_RECEIPT')
        self.assertTrue(all(report['checks'].values()))
        ids = self.server.request_ids
        self.assertNotEqual(ids[0], ids[1])
        self.assertEqual(ids[2], ids[3])
        self.assertNotIn('PRIVATE_', json.dumps(report))

    def test_missing_sources_cannot_pass_even_if_http_is_successful(self):
        self.server.doc = 'unrelated-document'
        report = run_checks(self.origin, self.settings, normal_repeats=1)
        self.assertEqual(report['verdict'], 'FAIL')
        self.assertFalse(report['normal'][0]['checks']['password_policy_source'])

    def test_missing_alert_fails(self):
        self.server.alerts = []
        report = run_checks(self.origin, self.settings, normal_repeats=1)
        self.assertEqual(report['verdict'], 'FAIL')
        self.assertFalse(report['checks']['admin_alert_once'])

    def test_db_request_link_must_match_not_just_table_counts(self):
        receipt = dict(self.receipt, linked=0)
        self.assertFalse(assess_db(receipt, 'T-fixture')['owner_and_keys_match'])
        self.assertFalse(assess_db(self.receipt, 'T-other')['api_db_ticket_matches'])

    def test_success_requires_two_database_snapshots(self):
        async def receipt(*args):
            return copy.deepcopy(self.receipt)
        with patch('live_check.vm_receipt', side_effect=receipt):
            report = run_checks(self.origin, self.settings, normal_repeats=1, with_vm_db=True)
        self.assertEqual(report['verdict'], 'PASS')
        self.assertIn('db_after_1', report)
        self.assertIn('db_after_2', report)

    def test_duplicate_database_row_causes_failure(self):
        async def receipt(*args):
            return dict(self.receipt, tickets=2)
        with patch('live_check.vm_receipt', side_effect=receipt):
            report = run_checks(self.origin, self.settings, normal_repeats=1, with_vm_db=True)
        self.assertEqual(report['verdict'], 'FAIL')

    def test_private_exception_text_is_never_in_report(self):
        with patch.object(Session, 'login', side_effect=RuntimeError('PRIVATE_PASSWORD_SENTINEL')):
            report = run_checks(self.origin, self.settings, normal_repeats=1)
        self.assertEqual(report['errors'], ['RuntimeError'])
        self.assertNotIn('PRIVATE_', json.dumps(report))
        self.assertEqual(report['verdict'], 'FAIL')

    def test_redirect_is_not_followed(self):
        status, _, _ = Session(self.origin).call('/redirect')
        self.assertEqual(status, 302)
        self.assertEqual(self.server.unexpected_requests, 0)

    def test_report_measurement_discards_answers_auth_and_contacts(self):
        record = measure_response(200, {'answer': 'PRIVATE_BODY_SENTINEL',
            'cookie': 'PRIVATE_COOKIE_SENTINEL', 'sources': [{'doc': 'password-policy',
            'text': 'PRIVATE_BODY_SENTINEL'}], 'ticket': None}, 1.0)
        self.assertNotIn('PRIVATE_', json.dumps(record))

    def test_slow_first_response_is_not_hidden_by_correct_answer(self):
        record = measure_response(200, {'route': '자동 답변', 'ticket': None,
            'sources': [{'doc': 'password-policy'}]}, 8.001)
        checks = assess_normal(record)
        self.assertFalse(checks['within_8_seconds'])
        self.assertTrue(checks['automatic_answer'])

    def test_origin_rejects_embedded_credentials_and_nonlocal_http(self):
        for origin in ['https://user:password@example.com', 'http://example.com',
                       'https://example.com?token=private', 'https://example.com/path']:
            with self.assertRaises(ValueError):
                validate_origin(origin)


if __name__ == '__main__':
    unittest.main()
