import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare', ROOT / 'tools/rag_prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads((ROOT / 'cases/source-inventory-mock.json').read_text())
        self.rows = prepare.inventory(self.snapshot)

    def test_required_cases(self):
        self.assertEqual([r['reasons'] for r in self.rows], [[], ['empty_document'],
            ['duplicate_doc_key'], ['duplicate_doc_key'], ['permission_unconfirmed'], []])
        self.assertIsNotNone(self.rows[4]['source_hash'])

    def test_hash_and_fences(self):
        before = self.rows[0]['source_hash']
        self.snapshot['document_responses']['mock-public']['text'] = self.snapshot['document_responses']['mock-public']['text'].replace('\r\n', '\n')
        self.assertEqual(before, prepare.inventory(self.snapshot)[0]['source_hash'])
        self.assertEqual([s for s, _ in self.rows[0]['sections']], ['서문', '점검'])

    def test_permission_conflict_and_body_failure(self):
        self.snapshot['document_responses']['mock-public']['access_level'] = 'it'
        self.assertIn('permission_conflict', prepare.inventory(self.snapshot)[0]['reasons'])
        del self.snapshot['document_responses']['mock-public']
        self.assertIn('body_unavailable', prepare.inventory(self.snapshot)[0]['reasons'])

    def test_report_has_no_restricted_content(self):
        report = prepare.render(self.snapshot, self.rows)
        for value in ['합성 제한 제목', '합성 제한 절', '합성 제한 내용', '조사 전용 합성 내용']:
            self.assertNotIn(value, report)


class RegressionTests(unittest.TestCase):
    def test_fenced_headings_only(self):
        for fence in ['```', '~~~', '````']:
            text = f'{fence}\n## fake\n{fence}\n'
            self.assertEqual(prepare.sections(text), [('본문', len(text))])

    def test_no_heading(self):
        self.assertEqual(prepare.sections('plain\n### nested\n'), [('본문', 17)])

    def test_empty_sections_preserved(self):
        self.assertEqual(prepare.sections('## first\n## second\n'), [('first', 0), ('second', 0)])

    def test_preamble_and_heading(self):
        self.assertEqual(prepare.sections('intro\n## real\nbody\n'), [('서문', 6), ('real', 5)])

    def test_whitespace_is_not_preamble(self):
        self.assertEqual(prepare.sections('\n \n## real\n'), [('real', 0)])

    def test_fence_does_not_close_on_short_or_other_marker(self):
        text = '````\n```\n## fake\n~~~\n````\n## real\n'
        self.assertEqual([s for s, _ in prepare.sections(text)], ['서문', 'real'])

    def test_common_mapping_and_unknown_rejection(self):
        s = {'list_response': {'docs': [{'name': 'password-policy'}, {'name': 'looks-admin'}]},
             'document_responses': {}}
        a, b = prepare.inventory(s)
        self.assertEqual(a['access_level'], 'all')
        self.assertIn('DATA-AND-DB', a['permission_evidence'][0]['source'])
        self.assertIn('permission_unconfirmed', b['reasons'])

    def test_provenance_and_determinism(self):
        s = json.loads((ROOT / 'cases/source-inventory-mock.json').read_text())
        a = prepare.inventory(s, clock=lambda: 'fixed')
        b = prepare.inventory(s, clock=lambda: 'fixed')
        self.assertEqual(prepare.render(s, a), prepare.render(s, b))
        self.assertEqual(a[0]['permission_evidence'][0]['field'], 'docs[0].access_level')
        self.assertIn('입력 스냅샷 SHA-256', prepare.render(s, a))
        self.assertEqual(a[0]['retrieved_at'], 'fixed')


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.env = {'DATA_API_URL': 'http://local.invalid', 'DATA_API_KEY': 'synthetic-test-only'}
        self.doc = {'name': 'x', 'title': 'restricted title', 'text': '## private\nrestricted body', 'access_level': 'it'}

    def collect(self, body_response):
        def fake(url, headers, timeout):
            self.assertEqual(headers, {'X-Api-Key': self.env['DATA_API_KEY']})
            self.assertEqual(timeout, 10)
            if url.endswith('/docs'):
                return 200, json.dumps({'docs': [{'name': 'x'}]})
            if isinstance(body_response, Exception):
                raise body_response
            return body_response
        return prepare.collect_api(self.env, fake, clock=lambda: 'fixed')

    def test_success_and_restricted_information(self):
        s = self.collect((200, json.dumps(self.doc)))
        rows = prepare.inventory(s)
        report = prepare.render(s, rows)
        self.assertEqual(rows[0]['access_level'], 'it')
        self.assertEqual(rows[0]['retrieved_at'], 'fixed')
        for secret in ['restricted title', 'restricted body', 'private', self.env['DATA_API_KEY']]:
            self.assertNotIn(secret, report)

    def test_http_error(self):
        s = self.collect((500, 'sensitive upstream body'))
        self.assertIn('http_error', prepare.inventory(s)[0]['reasons'])
        self.assertNotIn('sensitive', prepare.render(s, prepare.inventory(s)))

    def test_authentication_errors(self):
        for status in (401, 403):
            self.assertIn('authentication_failed', prepare.inventory(self.collect((status, 'secret')))[0]['reasons'])

    def test_timeout(self):
        self.assertIn('timeout', prepare.inventory(self.collect(TimeoutError('secret')))[0]['reasons'])

    def test_bad_json(self):
        self.assertIn('invalid_json', prepare.inventory(self.collect((200, '{private')))[0]['reasons'])

    def test_invalid_body_shapes_and_missing_fields(self):
        for body in [[], None, {}, {'text': 12}, {'text': 'body'}, {'name': 'wrong', 'text': 'body', 'title': 'title'}]:
            with self.subTest(body=body):
                row = prepare.inventory(self.collect((200, json.dumps(body))))[0]
                self.assertTrue(row['reasons'])

    def test_list_failure_is_not_empty_success(self):
        for status, payload in [(401, 'private'), (500, 'private'), (200, '{'), (200, '[]'), (200, '{}'), (200, '{"docs":[{}]}')]:
            with self.subTest(status=status, payload=payload):
                with self.assertRaises(prepare.InventoryError) as caught:
                    prepare.collect_api(self.env, lambda *a: (status, payload))
                self.assertNotIn('private', str(caught.exception))

    def test_invalid_configuration_never_calls_transport(self):
        for base in ['', 'http://user:password@host', 'http://host?key=secret']:
            with self.assertRaises(prepare.InventoryError):
                prepare.collect_api(dict(self.env, DATA_API_URL=base), lambda *a: self.fail('HTTP called'))

    def test_doc_name_is_one_encoded_path_segment(self):
        calls = []
        def fake(url, *args):
            calls.append(url)
            return (200, '{"docs":[{"name":"a/b?c"}]}') if len(calls) == 1 else (404, '')
        prepare.collect_api(self.env, fake)
        self.assertEqual(calls[1], 'http://local.invalid/docs/a%2Fb%3Fc')

    def test_cli_api_uses_injected_transport(self):
        from unittest.mock import patch
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as directory:
            output = Path(directory) / 'report.md'
            with patch.dict('os.environ', self.env):
                prepare.main(['inventory', '--source', 'api', '--output', str(output)],
                             transport=lambda *a: (200, '{"docs":[]}'))
            self.assertIn('모드: api', output.read_text())

    def test_key_echo_is_redacted(self):
        from unittest.mock import patch
        s = self.collect((200, json.dumps(dict(self.doc, title=self.env['DATA_API_KEY'], access_level='all'))))
        with patch.dict('os.environ', self.env):
            self.assertNotIn(self.env['DATA_API_KEY'], prepare.render(s, prepare.inventory(s)))


class TransportTests(unittest.TestCase):
    def test_urllib_http_and_network_errors_are_sanitized(self):
        from urllib.error import HTTPError, URLError
        env = {'DATA_API_URL': 'http://local.invalid', 'DATA_API_KEY': 'synthetic-only'}
        for failure, code in [(HTTPError('secret', 403, 'secret', {}, None), 'authentication_failed'),
                              (URLError(TimeoutError('secret')), 'timeout'),
                              (URLError('secret'), 'transport_error')]:
            def fake(*args):
                raise failure
            with self.assertRaises(prepare.InventoryError) as caught:
                prepare.collect_api(env, fake)
            self.assertEqual(str(caught.exception), code)
            if isinstance(failure, HTTPError):
                failure.close()

    def test_standard_transport_without_network(self):
        from unittest.mock import patch, MagicMock
        response = MagicMock()
        response.__enter__.return_value.status = 200
        response.__enter__.return_value.read.return_value = b'{"docs":[]}'
        with patch.object(prepare.request, 'build_opener') as build:
            build.return_value.open.return_value = response
            self.assertEqual(prepare.http_transport('http://local.invalid/docs', {}, 10), (200, b'{"docs":[]}'))
            req = build.return_value.open.call_args.args[0]
            self.assertEqual(req.get_method(), 'GET')
            self.assertIsNone(prepare.NoRedirect().redirect_request(None, None, 302, '', {}, 'http://other.invalid'))

    def test_cr_normalization(self):
        self.assertEqual(prepare.normalize('a\rb\r\nc'), 'a\nb\nc')


class SecurityTests(unittest.TestCase):
    def collect_echo(self, field='title', level='all', default=False):
        from unittest.mock import patch
        key = 'injected-synthetic-credential'
        env = {'DATA_API_URL': 'http://local.invalid', 'DATA_API_KEY': key}
        doc = {'name': 'x', 'title': key, 'text': '## private section\nprivate body', 'access_level': level}
        doc[field] = key
        def fake(url, headers, timeout):
            self.assertEqual(headers['X-Api-Key'], key)
            return 200, json.dumps({'docs': [{'name': 'x'}]} if url.endswith('/docs') else doc)
        with patch.dict('os.environ', env if default else {'DATA_API_KEY': 'different-global-credential'}):
            snapshot = prepare.collect_api(None if default else env, fake, clock=lambda: 'fixed')
            rows = prepare.inventory(snapshot)
            report = prepare.render(snapshot, rows)
        self.assertNotIn(key, json.dumps(snapshot))
        self.assertNotIn(key, report)
        self.assertEqual(rows[0]['source_hash'], prepare.digest(prepare.normalize(doc['text']).encode()))
        return rows, report

    def test_injected_key_differs_from_global(self):
        rows, _ = self.collect_echo()
        self.assertEqual(rows[0]['access_level'], 'all')

    def test_default_environment_key_in_title(self):
        self.collect_echo(default=True)

    def test_key_in_permission_metadata(self):
        rows, _ = self.collect_echo(field='access_level')
        self.assertIn('permission_unconfirmed', rows[0]['reasons'])

    def test_key_in_error_message(self):
        from unittest.mock import patch
        import io
        from contextlib import redirect_stdout, redirect_stderr
        key = 'error-synthetic-credential'
        output = io.StringIO()
        def fake(*args):
            raise OSError(key)
        with redirect_stdout(output), redirect_stderr(output), patch.dict('os.environ', {'DATA_API_KEY': 'different'}):
            with self.assertRaises(prepare.InventoryError) as caught:
                prepare.collect_api({'DATA_API_URL': 'http://local.invalid', 'DATA_API_KEY': key}, fake)
        self.assertNotIn(key, str(caught.exception) + output.getvalue())

    def test_api_restricted_fields_absent_from_snapshot(self):
        _, report = self.collect_echo(level='it')
        self.assertNotIn('private section', report)
        self.assertNotIn('private body', report)

    def test_mock_key_removed_before_hash_serialization(self):
        from unittest.mock import patch
        key = 'mock-synthetic-credential'
        snapshot = {'list_response': {'docs': [{'name': 'x', 'access_level': 'all'}]},
                    'document_responses': {'x': {'name': 'x', 'title': key, 'text': '## ' + key + '\nbody'}}}
        rows = prepare.inventory(snapshot)
        original_hash = rows[0]['source_hash']
        dumps = prepare.json.dumps
        serialized = []
        def spy(value, *args, **kwargs):
            result = dumps(value, *args, **kwargs)
            serialized.append(result)
            return result
        with patch.dict('os.environ', {'DATA_API_KEY': key}), patch.object(prepare.json, 'dumps', side_effect=spy):
            report = prepare.render(snapshot, rows)
        self.assertTrue(serialized)
        self.assertTrue(all(key not in value for value in serialized))
        self.assertNotIn(key, report)
        self.assertEqual(rows[0]['source_hash'], original_hash)
        self.assertEqual(rows[0]['access_level'], 'all')

    def test_api_key_in_body_hash_preserved(self):
        self.collect_echo(field='text')


if __name__ == '__main__':
    unittest.main()
