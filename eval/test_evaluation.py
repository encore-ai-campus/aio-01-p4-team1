import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'rag'))
from rag_evaluate import evaluate, stats, compare_conditions

class EvaluationTests(unittest.TestCase):
    def setUp(self):
        q={'id':'F1','question':'synthetic','kind':'answer','source_verified':True,'status':'frozen','source_hash':'fake-hash','access_levels':['all'],'expected_doc':'d','expected_section':'s','verified_required_quotes':['answer']}
        self.cases={'version':'fake-v1','questions':[q]}
        condition={'source_hashes':{'d':'fake-hash'},'access_levels':[['all']], 'model':'text-embedding-3-large','dimensions':3072,'distance':'cosine','top_k':3,'questions_version':'fake-v1','repeats':3,'overlap':0,'environment':'fake','settings_version':'fake-v1'}
        self.bundle={'mode':'fake','conditions':{'section':copy.deepcopy(condition),'300':copy.deepcopy(condition)},'doc_access':{'d':'all'},'records':{}}
        for method in ('section','300'):
            for i in range(1,4):
                self.bundle['records'][f'{method}:F1:{i}']={'http_status':200,'response':{'ok':True,'evidence':[{'doc':'d','section':'s','text':'answer','score':.5}],'reason':None},'search_ms':i}
    def result(self):
        return evaluate(self.cases,3,self.bundle)['methods']['section']
    def test_hit(self):
        x=self.result();self.assertEqual(x['hit_at_3']['numerator'],3);self.assertEqual(x['mrr']['value'],1);self.assertEqual(x['evidence_coverage']['value'],1)
    def test_mrr_second_rank_and_failure(self):
        other={'doc':'other','section':'s','text':'other','score':.8}
        for r in self.bundle['records'].values():
            r['response']['evidence'].insert(0,other)
        r=self.bundle['records']['section:F1:2']
        r.update(http_status=503,response={'ok':False,'evidence':[],'reason':'search_unavailable'})
        x=self.result()
        self.assertEqual(x['mrr']['numerator'],1)
        self.assertEqual(x['mrr']['denominator'],3)
        self.assertEqual(x['mrr']['value'],1/3)
    def test_section_miss(self):
        self.cases['questions'][0]['expected_section']='other';self.assertEqual(self.result()['section_hit_at_3']['value'],0)
    def test_doc_miss(self):
        self.cases['questions'][0]['expected_doc']='other'
        for c in self.bundle['conditions'].values():c['source_hashes']['other']='fake-hash'
        self.assertEqual(self.result()['hit_at_3']['value'],0)
    def test_empty(self):
        for r in self.bundle['records'].values():r['response']={'ok':True,'evidence':[],'reason':'no_evidence'}
        x=self.result();self.assertEqual(x['response_counts']['empty'],3);self.assertEqual(x['hit_at_3']['value'],0)
    def test_partial_failure(self):
        r=self.bundle['records']['section:F1:2'];r.update(http_status=503,response={'ok':False,'evidence':[],'reason':'search_unavailable'})
        x=self.result();self.assertEqual(x['hit_at_3']['denominator'],3);self.assertEqual(x['response_counts']['failure'],1)
    def test_permission_leak(self):
        self.bundle['doc_access']['d']='it';self.assertEqual(self.result()['permission_leaks']['numerator'],3)
    def test_time_and_missing(self):
        x=self.result();self.assertEqual(x['measurements']['search_ms'],{'N':3,'median':2,'p95':3,'max':3});self.assertIsNone(x['measurements']['cost']['max']);self.assertEqual(x['missing_measurements']['cost'],3)
    def test_draft(self):
        self.cases['questions'][0]['status']='draft';x=self.result();self.assertEqual(x['hit_at_3']['denominator'],0);self.assertEqual(len(x['excluded']),3)
    def test_admin(self):
        self.cases['questions'][0]['kind']='admin_pending';self.assertEqual(self.result()['excluded'][0]['reason'],'admin_source_unavailable')
    def test_no_answer(self):
        self.cases['questions'][0]['kind']='no_answer'
        self.bundle['records']['section:F1:1']['incorrect_auto_answer']=True
        x=self.result();self.assertEqual(x['no_answer_incorrect']['numerator'],1);self.assertEqual(x['no_answer_incorrect']['denominator'],1);self.assertEqual(x['hit_at_3']['denominator'],0)
    def test_conditions_mismatch(self):
        self.bundle['conditions']['300']['dimensions']=1
        with self.assertRaises(ValueError):self.result()
    def test_stats_boundaries(self):
        self.assertIsNone(stats([])['p95']);self.assertEqual(stats([0])['p95'],0);self.assertEqual(stats(list(range(1,21)))['p95'],19)
        for v in (-1,True,float('nan'),float('inf')):
            with self.assertRaises(ValueError):stats([v])
    def test_existing_candidates_unfrozen(self):
        p=Path(__file__).resolve().parents[1]/'cases/rag-search.json'
        x=evaluate(json.loads(p.read_text()));self.assertEqual(len(x['methods']['section']['excluded']),48)
    def test_no_results_excluded(self):
        self.bundle['records']={};self.assertEqual(self.result()['hit_at_3']['denominator'],0)

class ReviewRegressionTests(unittest.TestCase):
    setUp = EvaluationTests.setUp
    result = EvaluationTests.result
    ref = 'sha256:' + 'a'*64
    def metadata(self, names=None):
        import hashlib
        names = names or ['s', 'another']
        for key,r in self.bundle['records'].items():
            e=r['response']['evidence'][0];e['section']=' / '.join(names)
            r['evidence_observations']=[{'rank':1,'doc':'d','content_hash':hashlib.sha256(e['text'].encode()).hexdigest(),
                'metadata':{'chunking':key.split(':')[0],'chunking_version':'p0-2-v1','source_hash':'fake-hash','source_range':[0,10],'included_sections':names}}]
    def test_invalid_quotes(self):
        for value in ('answer',3,{},None,[],[''],[' '],['answer',None]):
            with self.subTest(value=value):
                self.cases['questions'][0]['verified_required_quotes']=value
                with self.assertRaises(ValueError):self.result()
    def test_draft_invalid_quotes_excluded(self):
        self.cases['questions'][0].update(status='draft',verified_required_quotes='answer')
        self.assertEqual(self.result()['hit_at_3']['denominator'],0)
    def test_multiple_required_quotes(self):
        self.cases['questions'][0]['verified_required_quotes']=['answer','missing']
        self.assertEqual(self.result()['evidence_coverage']['value'],0)
    def test_combined_section_hit(self):
        self.metadata();self.assertEqual(self.result()['section_hit_at_3']['value'],1)
        self.assertEqual(evaluate(self.cases,3,self.bundle)['methods']['300']['section_hit_at_3']['value'],1)
    def test_similar_section_no_hit(self):
        self.metadata(['s-extra','another']);self.assertEqual(self.result()['section_hit_at_3']['value'],0)
    def test_missing_and_untrusted_metadata(self):
        for mutation in ('missing','hash','range','source','duplicate'):
            with self.subTest(mutation=mutation):
                self.metadata()
                for r in self.bundle['records'].values():
                    if mutation=='missing':r.pop('evidence_observations')
                    elif mutation=='hash':r['evidence_observations'][0]['content_hash']='wrong'
                    elif mutation=='source':r['evidence_observations'][0]['metadata']['source_hash']='wrong'
                    elif mutation=='duplicate':r['evidence_observations']*=2
                    else:r['evidence_observations'][0]['metadata']['source_range']=[10,0]
                self.assertEqual(self.result()['section_hit_at_3']['value'],0)
    def test_other_doc_no_section_hit(self):
        self.metadata()
        for r in self.bundle['records'].values():r['response']['evidence'][0]['doc']='other'
        self.assertEqual(self.result()['section_hit_at_3']['value'],0)
    def test_count_validation(self):
        for field in ('embedding_tokens','chunk_count'):
            for value in (1.5,-1,float('nan'),float('inf'),'2',True):
                self.bundle['records']['section:F1:1']={**self.bundle['records']['section:F1:1'],field:value}
                with self.subTest(field=field,value=value):
                    with self.assertRaises(ValueError):self.result()
                self.bundle['records']['section:F1:1'].pop(field)
    def test_cost_source_required(self):
        r=self.bundle['records']['section:F1:1'];r['cost']=.01
        with self.assertRaises(ValueError):self.result()
        r['measurement_provenance']={'cost':{'kind':'actual','source_ref':self.ref,'currency':'USD'}}
        with self.assertRaises(ValueError):self.result()
    def test_actual_estimated_cost_groups(self):
        for i,kind in ((1,'actual'),(2,'estimated')):
            r=self.bundle['records'][f'section:F1:{i}'];r['cost']=.01
            r['measurement_provenance']={'cost':{'kind':kind,'source_ref':self.ref,'currency':'USD','unit_price':.001}}
        x=self.result();self.assertIsNone(x['measurements']['cost']['median'])
        self.assertEqual(set(x['measurement_groups']['cost']),{'actual:USD','estimated:USD'})
    def test_observation_tracking_no_body(self):
        r=self.bundle['records']['section:F1:1'];r.update(source_ref=self.ref,embedding_ms=1,db_ms=2,embedding_tokens=0,chunk_count=3,cost=0)
        r['measurement_provenance']={f:{'kind':'actual','source_ref':self.ref}for f in ('embedding_tokens','chunk_count','cost')}
        r['measurement_provenance']['cost'].update(currency='USD',calculation_ref=self.ref)
        x=self.result()['observations'][0]
        self.assertEqual(x['method'],'section');self.assertEqual(x['measurements']['embedding_tokens'],0)
        self.assertEqual(x['evidence'],[{'rank':1,'doc':'d','section':'s','score':.5}])
        self.assertEqual(x['source_ref'],self.ref)
        self.assertTrue(all('text' not in e for e in x['evidence']))
        self.assertEqual(x['model'],'text-embedding-3-large');self.assertEqual(x['settings_version'],'fake-v1')
    def test_restricted_section_redaction(self):
        self.bundle['doc_access']['d']='it'
        self.assertEqual(self.result()['observations'][0]['evidence'][0]['section'],'[restricted_or_unknown]')
    def test_unsafe_reference_rejected(self):
        self.bundle['records']['section:F1:1']['source_ref']='https://private/?key=not-a-key'
        with self.assertRaises(ValueError):self.result()
    def test_cli_duplicate_keys_no_output_changes(self):
        import subprocess,tempfile,os
        duplicate_cases = copy.deepcopy(self.cases)
        duplicate_cases['questions'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate_question_id'):
            evaluate(duplicate_cases, 3, self.bundle)
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            p=Path(tmp);cases=p/'cases.json';results=p/'results.json';output=p/'output.md';output.write_text('sentinel')
            cases.write_text(json.dumps(self.cases));raw=json.dumps(self.bundle)
            item=json.dumps(self.bundle['records']['section:F1:1']);needle='"section:F1:1": '+item
            results.write_text(raw.replace(needle,needle+', '+needle,1))
            args=[sys.executable,str(root/'rag/rag_verify.py'),'evaluate','--cases',str(cases),'--results',str(results),'--output',str(output)]
            x=subprocess.run(args,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            self.assertEqual(x.returncode,2);self.assertIn('duplicate_json_key',x.stderr);self.assertEqual(output.read_text(),'sentinel')
    def test_cli_idempotent_append(self):
        import subprocess,tempfile,os
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            p=Path(tmp);cases=p/'cases.json';output=p/'output.md';cases.write_text(json.dumps(self.cases));output.write_text('sentinel')
            args=[sys.executable,str(root/'rag/rag_verify.py'),'evaluate','--cases',str(cases),'--output',str(output)]
            for _ in range(2):
                x=subprocess.run(args,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));self.assertEqual(x.returncode,0,x.stderr)
            self.assertTrue(output.read_text().startswith('sentinel'));self.assertEqual(output.read_text().count('<!-- rag-evaluation:'),1)
