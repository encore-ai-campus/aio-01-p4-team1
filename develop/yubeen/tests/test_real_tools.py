"""Real-path protocols with injected transports/cursors; no real DB or OpenAI."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import rag_contract
import rag_db
import rag_evaluate
import rag_index
import rag_measure
import rag_verify


class RealEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.hash = 'a'*64
        self.cases = dict(version='approved-test-v1', questions=[dict(id='Q1',question='synthetic',kind='answer',
            status='frozen',source_verified=True,source_hash=self.hash,access_levels=['all'],
            expected_doc='public',expected_section='section',verified_required_quotes=['answer'])])
        self.inventory = dict(mode='postgres',documents=[dict(doc_key='public',source_hash=self.hash,
            access_level='all',chunks=[dict(chunking='section')])])
        self.response = dict(ok=True,evidence=[dict(doc='public',section='section',text='answer',score=.8)],reason=None)

    def run_collection(self, method='section', search=None):
        inv = copy.deepcopy(self.inventory)
        inv['documents'][0]['chunks'][0]['chunking']=method
        ticks=iter(range(6))
        return rag_measure.collect(self.cases,inv,method,3,'isolated-test',
            search=search or (lambda body:(200,self.response)),clock=lambda:next(ticks))

    def bundle(self):
        return rag_measure.merge(self.run_collection(),self.run_collection('300'))

    def test_real_results_metrics_and_time(self):
        result=rag_evaluate.evaluate(self.cases,3,self.bundle())
        self.assertEqual(result['mode'],'real')
        self.assertEqual(result['execution_claim'],'imported_observations')
        section=result['methods']['section']
        self.assertEqual(section['recall_at_3']['value'],1)
        self.assertEqual(section['mrr']['value'],1)
        self.assertEqual(section['measurements']['search_ms']['N'],3)
        self.assertNotIn('answer',json.dumps(section['observations']))

    def test_real_failures_count_as_misses(self):
        failure=lambda body:(503,dict(ok=False,evidence=[],reason='search_unavailable'))
        a=self.run_collection(search=failure); b=self.run_collection('300',search=failure)
        r=rag_evaluate.evaluate(self.cases,3,rag_measure.merge(a,b))
        self.assertEqual(r['methods']['section']['recall_at_3']['value'],0)
        self.assertEqual(r['methods']['section']['response_counts']['failure'],3)

    def test_real_unknown_permission_rejected(self):
        bundle=self.bundle(); bundle['doc_access']={}
        with self.assertRaises(ValueError):rag_evaluate.evaluate(self.cases,3,bundle)

    def test_real_provenance_required(self):
        bundle=self.bundle(); next(iter(bundle['records'].values())).pop('source_ref')
        with self.assertRaises(ValueError):rag_evaluate.evaluate(self.cases,3,bundle)

    def test_draft_no_service_calls(self):
        self.cases['questions'][0]['status']='draft'; search=Mock()
        with self.assertRaisesRegex(ValueError,'no_frozen_cases'):self.run_collection(search=search)
        search.assert_not_called()

    def test_wrong_index_method_rejected(self):
        with self.assertRaisesRegex(ValueError,'index_chunking_mismatch'):
            rag_measure.collect(self.cases,self.inventory,'300',3,'test')

    def test_mismatched_source_rejected(self):
        self.cases['questions'][0]['source_hash']='b'*64
        with self.assertRaisesRegex(ValueError,'case_source_mismatch'):self.run_collection()

    def test_comparison_conditions_cannot_change(self):
        a=self.run_collection(); b=self.run_collection('300'); b['condition']['environment']='other'
        with self.assertRaises(ValueError):rag_measure.merge(a,b)

    def test_bad_http_status_rejected(self):
        with self.assertRaises(ValueError):self.run_collection(search=lambda b:(401,{}))

    def test_sidecar_used_for_real_combined_section(self):
        response=copy.deepcopy(self.response);response['evidence'][0]['section']='section / next'
        def observe(rows,levels):
            return [dict(rank=1,doc='public',content_hash=hashlib.sha256(rows[0]['text'].encode()).hexdigest(),
                metadata=dict(chunking='300',chunking_version='p0-2-v1',source_hash=self.hash,
                              included_sections=['section','next'],source_range=[0,10]))]
        inv=copy.deepcopy(self.inventory);inv['documents'][0]['chunks'][0]['chunking']='300'
        chars=rag_measure.collect(self.cases,inv,'300',3,'isolated-test',
            search=lambda b:(200,response),observe=observe)
        result=rag_evaluate.evaluate(self.cases,3,rag_measure.merge(self.run_collection(),chars))
        self.assertEqual(result['methods']['300']['section_hit_at_3']['value'],1)

    def test_real_cli_json_and_markdown_reports(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path=Path(tmp);cases=path/'cases.json';bundle=path/'results.json'
            cases.write_text(json.dumps(self.cases));bundle.write_text(json.dumps(self.bundle()))
            self.assertEqual(rag_measure.main(['report','--cases',str(cases),'--results',str(bundle),
                '--output',str(path/'report.json')]),0)
            import subprocess
            result=subprocess.run([sys.executable,str(ROOT/'tools/rag_verify.py'),'evaluate',
                '--cases',str(cases),'--results',str(bundle),'--output',str(path/'report.md')],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('실제 관측 입력 집계',(path/'report.md').read_text())

    def test_external_gate_no_network(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp, patch('rag_measure.http_search') as search:
            self.assertEqual(rag_measure.main(['collect','--cases','missing','--method','section',
                '--environment','test','--output',str(Path(tmp)/'out.json')]),1)
            search.assert_not_called()

    def test_default_index_settings_unchanged(self):
        settings=rag_index.load_settings(); settings['chunking']='300'
        with self.assertRaises(ValueError):rag_index.validate_settings(settings)
        self.assertEqual(rag_index.validate_settings(settings,comparison=True)['chunking'],'300')

    def test_comparison_index_changes_only_explicit_setting(self):
        snapshot=dict(list_response={'docs':[dict(name='test',access_level='all')]},
            document_responses={'test':dict(name='test',title='test',text='x'*610,access_level='all')})
        settings=rag_index.load_settings();settings['chunking']='300';store=rag_index.MockStore()
        a=rag_index.index_snapshot(snapshot,rag_verify.mock_embed,store,settings,comparison=True)
        b=rag_index.index_snapshot(snapshot,rag_verify.mock_embed,store,settings,comparison=True)
        self.assertEqual(a['documents'][0]['chunk_count'],3)
        self.assertEqual(b['counts']['skipped'],1)


class DatabaseSnapshotTests(unittest.TestCase):
    def connection(self, *, content_hash=None, dims=3072, number=0):
        cursor=Mock();cursor.__enter__=Mock(return_value=cursor);cursor.__exit__=Mock(return_value=False)
        cursor.fetchone.side_effect=[('0.8.0',),('vector(3072)',)]
        cursor.fetchall.side_effect=[ [('public','title','all','/docs/public','a'*64)],
            [('public',number,'section','content',content_hash or hashlib.sha256(b'content').hexdigest(),
              'text-embedding-3-large',{'chunking':'section'},dims,'[1,2]')] ]
        conn=Mock();conn.cursor.return_value=cursor
        return conn

    def test_snapshot_redacts_body_vector_and_identity(self):
        result=rag_db.snapshot(self.connection());text=json.dumps(result)
        self.assertNotIn('"content"',text);self.assertNotIn('[1,2]',text);self.assertNotIn('"title"',text)
        self.assertEqual(result['documents'][0]['chunk_count'],1)

    def test_bad_hash_dimension_and_sequence(self):
        for kw in (dict(content_hash='wrong'),dict(dims=3),dict(number=1)):
            with self.subTest(kw=kw),self.assertRaises(ValueError):rag_db.snapshot(self.connection(**kw))

    def test_compare_survives_db_id_changes_and_reports_updates(self):
        before=rag_db.snapshot(self.connection());after=copy.deepcopy(before);after['captured_at']='later'
        self.assertTrue(rag_db.compare(before,after)['same_inventory'])
        after['documents'][0]['source_hash']='changed'
        self.assertEqual(rag_db.compare(before,after)['changed'],['public'])
        self.assertFalse(rag_db.compare(before,after)['actual_restart_observed'])

    def test_baseline_no_overwrite_and_owner_boundary(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path=Path(tmp)/'before.json';rag_db.write_new(path,{'ok':True})
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            with self.assertRaises(FileExistsError):rag_db.write_new(path,{})
        with self.assertRaises(ValueError):rag_db.output_path('/tmp/not-owned.json')

    def test_db_gate(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            self.assertEqual(rag_db.main(['snapshot','--output',str(Path(tmp)/'out.json')]),1)


class IntegrationContractTests(unittest.TestCase):
    def setUp(self):
        self.e=dict(doc='public',section='s',text='safe',score=.7)
        self.record=dict(access_levels=['all'],search_status=200,
            search_response=dict(ok=True,evidence=[self.e],reason=None),llm_evidence=[self.e],
            support_response=dict(request_id='test',route='자동 답변',answer='safe',
                sources=[dict(doc='public',section='s',score=.7)],ticket=None,agents={},security={}))

    def test_support_and_llm_checked(self):
        self.assertTrue(rag_contract.check(self.record,{'public':'all'})['llm_boundary_observed'])

    def test_restricted_evidence_blocked(self):
        with self.assertRaisesRegex(ValueError,'evidence_permission_leak'):
            rag_contract.check(self.record,{'public':'it'})
        self.record['access_levels']=['all','it']
        self.assertTrue(rag_contract.check(self.record,{'public':'it'})['ok'])

    def test_llm_and_sources_cannot_add_other_documents(self):
        for key in ('llm_evidence','sources'):
            record=copy.deepcopy(self.record)
            if key=='llm_evidence':record[key][0]['doc']='private'
            else:record['support_response'][key][0]['doc']='private'
            with self.assertRaises(ValueError):rag_contract.check(record,{'public':'all','private':'it'})

    def test_missing_llm_observation_not_claimed(self):
        self.record.pop('llm_evidence')
        self.assertFalse(rag_contract.check(self.record,{'public':'all'})['llm_boundary_observed'])

    def test_empty_and_failure_require_handoff(self):
        for status,body in ((200,dict(ok=True,evidence=[],reason='no_evidence')),
                            (503,dict(ok=False,evidence=[],reason='search_unavailable'))):
            record=copy.deepcopy(self.record);record.update(search_status=status,search_response=body,llm_evidence=[])
            record['support_response']['sources']=[]
            with self.assertRaises(ValueError):rag_contract.check(record,{'public':'all'})
            record['support_response']['route']='담당자 이관'
            self.assertTrue(rag_contract.check(record,{'public':'all'})['ok'])
