import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_chunks', ROOT / 'tools/rag_prepare.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ChunkingTests(unittest.TestCase):
    def chunk(self, text, method='section', key='x', level='all'):
        return p.chunk_document(key, '제목', text, level, method)

    def test_sections_and_subheading(self):
        result = self.chunk('## 하나\n내용\n### 하위\n내용2\n## 둘\n끝')
        self.assertEqual(len(result['chunks']), 2)
        self.assertIn('### 하위', result['chunks'][0]['content'])
        self.assertTrue(result['coverage_with_exclusions'])

    def test_preamble_and_plain(self):
        self.assertEqual([c['section'] for c in self.chunk('서문\n## 절\n내용')['chunks']], ['서문', '절'])
        self.assertEqual(self.chunk('일반 본문')['chunks'][0]['section'], '본문')

    def test_empty_sections_retained_but_not_chunked(self):
        r = self.chunk('## 빈 절\n## 정상\n내용\n## 마지막\n')
        self.assertEqual(len(r['sections']), 3)
        self.assertEqual(len(r['excluded']), 2)
        self.assertEqual(len(r['chunks']), 1)
        self.assertTrue(r['coverage_with_exclusions'])

    def test_fences_lists_and_tables_preserved(self):
        text = '## 절\n- 목록\n| 열 | 값 |\n| -- | -- |\n```\n## 가짜\n```\n'
        r = self.chunk(text)
        self.assertEqual(len(r['chunks']), 1)
        self.assertTrue(r['chunks'][0]['content'].endswith(text))

    def test_unicode_boundary(self):
        text = '🙂가'*301
        r = self.chunk(text, '300')
        self.assertEqual([c['body_length'] for c in r['chunks']], [300, 300, 2])
        self.assertEqual(r['chunks'][0]['metadata']['source_range'], [0, 300])

    def test_cross_section_mapping(self):
        text = '## 하나\n짧은 내용\n## 둘\n다음 내용'
        r = self.chunk(text, '300')
        self.assertEqual(r['chunks'][0]['metadata']['included_sections'], ['하나', '둘'])

    def test_both_methods_preserve_ranges_hashes_order(self):
        text = '서문\r\n## 하나\r\n'+'한글🙂'*150+'\r\n## 둘\r\n끝'
        normalized = p.normalize(text)
        for method in ('section', '300'):
            r = self.chunk(text, method)
            restored = ''
            for i, c in enumerate(r['chunks']):
                a, b = c['metadata']['source_range']
                self.assertEqual(c['chunk_no'], i)
                self.assertEqual(c['content_hash'], p.digest(c['content'].encode()))
                self.assertEqual(c['metadata']['source_hash'], p.digest(normalized.encode()))
                self.assertEqual(c['content'][c['prefix_length']:], normalized[a:b])
                restored += normalized[a:b]
            self.assertEqual(restored, normalized)

    def test_document_boundaries_and_permissions(self):
        for key, level in [('a', 'all'), ('b', 'it')]:
            for c in self.chunk('## 절\n본문', key=key, level=level)['chunks']:
                self.assertEqual((c['doc_key'], c['access_level']), (key, level))

    def test_oversized_section_is_not_truncated(self):
        r = self.chunk('## 긴 절\n'+'가'*3000)
        self.assertEqual(r['chunks'], [])
        self.assertEqual(r['rejected'][0]['reason'], 'oversized_content_review')
        self.assertTrue(r['coverage_with_exclusions'])

    def test_comparison_permissions_and_no_leaks(self):
        fixture = json.loads((ROOT/'cases/chunk-comparison-mock.json').read_text())
        report = p.compare_snapshot(fixture)
        for value in ['제한 제목', '제한 절', '합성 제한 본문', '미확인 합성 내용']:
            self.assertNotIn(value, report)
        self.assertIn('permission_unconfirmed', report)
        self.assertIn('"methods": {}', report)

    def test_key_is_removed_before_comparison_serialization(self):
        key = 'synthetic-comparison-key'
        fixture={'list_response':{'docs':[{'name':'x','access_level':'all'}]},
                 'document_responses':{'x':{'name':'x','title':key,'text':'## '+key+'\nbody'}}}
        original = p.json.dumps
        def checked(value, *args, **kwargs):
            serialized = original(value, *args, **kwargs)
            self.assertNotIn(key, serialized)
            return serialized
        with patch.object(p.json, 'dumps', side_effect=checked):
            self.assertNotIn(key, p.compare_snapshot(fixture, secrets=(key,)))

    def test_cli_and_determinism(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as d:
            output=Path(d)/'report.md'
            args=['compare-chunks','--source','mock','--input',str(ROOT/'cases/chunk-comparison-mock.json'),
                  '--baseline','section','--candidate','300','--output',str(output)]
            p.main(args)
            first=output.read_bytes()
            p.main(args)
            self.assertEqual(first,output.read_bytes())

    def test_api_comparison_uses_one_snapshot_and_fake_transport(self):
        calls=[]
        def fake(url,*args):
            calls.append(url)
            return 200, json.dumps({'docs':[{'name':'x','access_level':'all'}]} if url.endswith('/docs') else
                                   {'name':'x','title':'합성','text':'## 절\n내용'})
        with patch.dict('os.environ',{'DATA_API_URL':'http://local.invalid','DATA_API_KEY':'synthetic-only'}):
            report=p.collect_api(transport=fake,processor=p.compare_snapshot)
        self.assertEqual(len(calls),2)
        self.assertIn('모드: api',report)
        self.assertIn('"section": {',report)
        self.assertIn('"300": {',report)

    def test_question_drafts_and_admin_pending(self):
        data=json.loads((ROOT/'cases/rag-search.json').read_text())
        self.assertEqual(len(data['questions']),16)
        self.assertEqual(data['status'],'draft_not_frozen')
        for q in data['questions']:
            self.assertFalse(q['source_verified'])
            if int(q['id'][1:])>=14:
                self.assertIsNone(q['question'])
                self.assertIsNone(q['expected_doc'])
        self.assertEqual([q['kind'] for q in data['questions'][11:13]],['no_answer','no_answer'])

    def test_unknown_permission_rejected_by_chunk_builder(self):
        with self.assertRaises(p.InventoryError):
            self.chunk('내용', level=None)

    def test_contract_examples(self):
        data=json.loads((ROOT/'cases/rag-search.json').read_text())
        self.assertEqual([c.get('http') for c in data['functional_cases'][:3]],[200,200,503])
        for name, levels in [('all',['all']),('it',['all','it'])]:
            request=json.loads((ROOT/f'requests/search-{name}.json').read_text())
            self.assertEqual(request['access_levels'],levels)
            self.assertEqual(request['top_k'],3)


class DefectRegressionTests(unittest.TestCase):
    def mixed_snapshot(self):
        return {'list_response': {'docs': [{'name': 'x', 'access_level': 'all'}]},
                'document_responses': {'x': {'name': 'x', 'title': 'title',
                'text': '## good\nok\n## long\n' + '가' * 3000}}}

    def test_partial_section_and_complete_candidate(self):
        doc = self.mixed_snapshot()['document_responses']['x']
        section = p.chunk_document('x', doc['title'], doc['text'], 'all', 'section')
        candidate = p.chunk_document('x', doc['title'], doc['text'], 'all', '300')
        self.assertEqual(section['status'], 'partial')
        self.assertEqual(len(section['chunks']), 1)
        self.assertEqual(section['chunk_coverage']['ranges'], [[0, 11]])
        self.assertEqual(section['coverage_accounting']['rejected_characters'], 3008)
        self.assertEqual(section['coverage_accounting']['chunk_characters'], 11)
        self.assertFalse(section['chunk_coverage']['covers_entire_source'])
        self.assertTrue(section['coverage_with_exclusions'])
        self.assertEqual(candidate['status'], 'complete')
        self.assertEqual(len(candidate['chunks']), 11)
        self.assertEqual(candidate['coverage_accounting']['rejected_characters'], 0)
        self.assertTrue(candidate['chunk_coverage']['covers_entire_source'])
        self.assertEqual(section['source_hash'], candidate['source_hash'])

    def test_all_rejected_state(self):
        result = p.chunk_document('x', 'title', '## long\n' + '가' * 3000, 'all', 'section')
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['chunk_coverage']['characters'], 0)
        self.assertTrue(result['reasons'])

    def test_intentional_exclusions_distinct_from_rejection(self):
        result = p.chunk_document('x', 'title', '## empty\n## good\nok', 'all', 'section')
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['coverage_accounting']['excluded_characters'], 9)
        self.assertEqual(result['coverage_accounting']['rejected_characters'], 0)
        self.assertFalse(result['chunk_coverage']['covers_entire_source'])
        self.assertTrue(result['coverage_accounting']['all_ranges_accounted'])

    def test_partial_report_and_cohort_statistics(self):
        report = p.compare_snapshot(self.mixed_snapshot())
        blocks = report.split('```json\n')
        row = json.loads(blocks[1].split('\n```')[0])[0]
        cohorts = json.loads(blocks[2].split('\n```')[0])
        self.assertEqual(row['status'], 'partial')
        self.assertIn('section:oversized_content_review', row['reasons'])
        self.assertEqual(cohorts['section']['complete']['document_count'], 0)
        self.assertEqual(cohorts['section']['complete']['body_lengths'], '미측정')
        self.assertEqual(cohorts['section']['partial']['chunk_count'], 1)
        self.assertEqual(cohorts['300']['complete']['chunk_count'], 11)

    def test_exact_300_and_301_unicode_boundaries(self):
        for char in ('가', '🙂'):
            for size, expected in [(300, [300]), (301, [300, 1])]:
                with self.subTest(char=char, size=size):
                    result = p.chunk_document('x', 'title', char * size, 'all', '300')
                    self.assertEqual([c['body_length'] for c in result['chunks']], expected)
                    self.assertTrue(result['chunk_coverage']['covers_entire_source'])

    def test_network_adapter_denied_before_transport(self):
        with patch.object(p, 'http_transport') as transport:
            with self.assertRaisesRegex(p.InventoryError, '^api_network_not_authorized$'):
                p.collect_api({'DATA_API_URL': 'http://local.invalid', 'DATA_API_KEY': 'synthetic'})
            transport.assert_not_called()

    def test_both_cli_api_commands_denied_by_default(self):
        import io
        from contextlib import redirect_stderr
        for command in ('inventory', 'compare-chunks'):
            err = io.StringIO()
            with redirect_stderr(err), patch.object(p, 'http_transport') as transport:
                with self.assertRaises(SystemExit) as caught:
                    p.main([command, '--source', 'api', '--output', str(ROOT/'Doc/never-written.md')])
                self.assertEqual(caught.exception.code, 2)
                self.assertEqual(err.getvalue().strip(), 'api_network_not_authorized')
                transport.assert_not_called()

    def test_explicit_permission_uses_fake_underlying_transport(self):
        env = {'DATA_API_URL': 'http://local.invalid', 'DATA_API_KEY': 'synthetic'}
        with patch.object(p, 'http_transport', return_value=(200, b'{"docs":[]}')) as fake:
            self.assertEqual(p.collect_api(env, allow_network=True)['mode'], 'api')
            fake.assert_called_once()

    def test_both_cli_allow_option_with_fake_transport_only(self):
        env = {'DATA_API_URL': 'http://local.invalid', 'DATA_API_KEY': 'synthetic'}
        for command in ('inventory', 'compare-chunks'):
            with patch.dict('os.environ', env), patch.object(p, 'http_transport', return_value=(200, b'{"docs":[]}')) as fake, patch.object(Path, 'write_text'):
                p.main([command, '--source', 'api', '--allow-network', '--output', str(ROOT/'Doc/never-written.md')])
                fake.assert_called_once()

    def test_denial_message_contains_no_configuration(self):
        import io
        from contextlib import redirect_stderr
        key = 'synthetic-private-denial-value'
        err = io.StringIO()
        with patch.dict('os.environ', {'DATA_API_URL': 'http://local.invalid', 'DATA_API_KEY': key}), redirect_stderr(err):
            with self.assertRaises(SystemExit):
                p.main(['inventory', '--source', 'api', '--output', str(ROOT/'Doc/never-written.md')])
        self.assertNotIn(key, err.getvalue())
        self.assertNotIn('local.invalid', err.getvalue())

    def test_functional_case_completeness(self):
        data = json.loads((ROOT/'cases/rag-search.json').read_text())
        cases = {c['kind']: c for c in data['functional_cases']}
        self.assertEqual(len(cases), 10)
        for kind in ('db_error', 'embedding_error', 'search_timeout'):
            self.assertEqual(cases[kind]['http'], 503)
            self.assertEqual(cases[kind]['response'], {'ok': False, 'evidence': [], 'reason': 'search_unavailable'})
        self.assertIsNone(cases['invalid_input']['http'])
        self.assertIsNone(cases['invalid_input']['response'])

    def test_tie_case_expected_order(self):
        cases = json.loads((ROOT/'cases/rag-search.json').read_text())['functional_cases']
        case = next(c for c in cases if c['kind'] == 'tie_order')
        ordered = sorted(case['synthetic_candidates'], key=lambda c: (c['distance'], c['doc'], c['chunk_no']))[:case['top_k']]
        self.assertEqual([{'doc': c['doc'], 'chunk_no': c['chunk_no']} for c in ordered], case['expected_order'])

    def test_claim_case_preserves_verified_permission(self):
        cases = json.loads((ROOT/'cases/rag-search.json').read_text())['functional_cases']
        case = next(c for c in cases if c['kind'] == 'admin_claim_no_escalation')
        self.assertIn('관리자', case['request']['query'])
        self.assertEqual(case['request']['access_levels'], case['verified_access_levels'])
        self.assertEqual(case['expected_access_levels'], ['all'])
        self.assertEqual(case['expected_allowed_candidate_access_levels'], ['all'])

    def test_evidence_draft_review_not_frozen(self):
        data = json.loads((ROOT/'cases/rag-search.json').read_text())
        self.assertEqual(data['status'], 'draft_not_frozen')
        for q in data['questions'][:11]:
            self.assertTrue(q['evidence_review']['same_draft_value_requires_source_review'])
            self.assertFalse(q['evidence_review']['separation_verified'])
            self.assertFalse(q['source_verified'])
        self.assertEqual(data['history'][-1]['phase'], 'before_search')


if __name__ == '__main__':
    unittest.main()
