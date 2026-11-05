import sys
from pathlib import Path
import unittest
import io
import json
from unittest.mock import patch
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import rag_search as s

class SearchAdapterTests(unittest.TestCase):
    def setUp(self):
        self.embed = Mock(return_value={'model':'text-embedding-3-large','embedding':[1.0]*3072})
        self.cursor = Mock(); self.cursor.fetchall.return_value=[('public','section','content',0.75)]
        self.connection = Mock(); self.connection.cursor.return_value=self.cursor
        self.repo=s.PgvectorSearchAdapter(self.connection)
    def run_search(self, **kw):
        return s.dispatch('query', ['all'], mode='adapter', adapter_enabled=True, embedder=self.embed, repository=self.repo, **kw)
    def test_vector_and_evidence(self):
        code,body=self.run_search(); self.assertEqual(code,200); self.assertEqual(body['evidence'],[{'doc':'public','section':'section','text':'content','score':0.75}]); self.embed.assert_called_once_with('query','text-embedding-3-large',3072)
    def test_dimension(self):
        self.embed.return_value['embedding']=[1]; self.assertEqual(self.run_search()[0],503); self.connection.cursor.assert_not_called()
    def test_nonfinite(self):
        for v in (float('nan'),float('inf'),True):
            self.embed.return_value['embedding']=[v]*3072; self.assertEqual(self.run_search()[0],503)
    def test_provider_fault(self):
        self.embed.side_effect=RuntimeError('private'); self.assertEqual(self.run_search(),s.unavailable())
    def test_sql_binding_filter_limit(self):
        self.run_search(); sql,params=self.cursor.execute.call_args.args
        self.assertIn('WHERE d.access_level = ANY(%s)',sql); self.assertIn('MATERIALIZED',sql); self.assertIn('c.embedding_model = %s',sql); self.assertIn('LIMIT %s',sql); self.assertEqual(params[0],['all']); self.assertEqual(params[-1],3); self.assertIn('doc_key ASC, chunk_no ASC',sql)
    def test_empty(self):
        self.cursor.fetchall.return_value=[]; self.assertEqual(self.run_search(),(200,{'ok':True,'evidence':[],'reason':'no_evidence'}))
    def test_db_fault_closes_cursor(self):
        self.cursor.execute.side_effect=RuntimeError('private'); self.assertEqual(self.run_search(),s.unavailable()); self.cursor.close.assert_called_once()
    def test_it_sql_filter_before_ranking(self):
        result=s.dispatch('query',['all','it'],mode='adapter',adapter_enabled=True,
                          embedder=self.embed,repository=self.repo)
        self.assertEqual(result[0],200)
        sql,params=self.cursor.execute.call_args.args
        self.assertIn('WITH allowed AS MATERIALIZED',sql)
        self.assertEqual(params[0],['all','it'])
        self.assertEqual(params[-1],3)
    def test_no_mock_fallback(self):
        mock=Mock(); self.assertEqual(s.dispatch('q',['all'],mode='adapter',mock_search=mock),s.unavailable()); mock.assert_not_called()
    def test_unset_mode(self):
        self.assertEqual(s.dispatch('q',['all']),s.unavailable())
    def test_topk(self):
        self.assertEqual(s.search_with_adapters('q',['all'],5,self.embed,self.repo),s.unavailable()); self.embed.assert_not_called()
    def test_model_mismatch(self):
        self.embed.return_value['model']='other'; self.assertEqual(self.run_search()[0],503)
    def test_zero_vector(self):
        self.embed.return_value['embedding']=[0]*3072; self.assertEqual(self.run_search()[0],503)
    def test_invalid_db_score(self):
        self.cursor.fetchall.return_value=[('public','section','content',float('nan'))]; self.assertEqual(self.run_search()[0],503)

class ResponseBoundaryRegressionTests(unittest.TestCase):
    row = {'doc':'public','section':'section','text':'content','score':0.5}
    def call(self, result):
        return s.search_with_adapters('query',['all'],3,
            lambda q,m,d:{'model':m,'embedding':[1.0]*d},
            Mock(search=Mock(return_value=result)))
    def test_overflow_rejected_not_truncated(self):
        self.assertEqual(self.call([self.row]*4),s.unavailable())
    def test_extra_fields_projected(self):
        row=dict(self.row,metadata={'internal':'private'},debug='private')
        self.assertEqual(self.call([row])[1]['evidence'],[self.row])
        self.assertIn('metadata',row)
    def test_missing_fields(self):
        for key in self.row:
            with self.subTest(key=key):
                row=dict(self.row); del row[key]; self.assertEqual(self.call([row]),s.unavailable())
    def test_field_types_and_empty_strings(self):
        for key in ('doc','section','text'):
            for value in (None,3,False,[],{},'', ' '):
                with self.subTest(key=key,value=value):
                    self.assertEqual(self.call([dict(self.row,**{key:value})]),s.unavailable())
    def test_bad_scores(self):
        for value in (float('nan'),float('inf'),-float('inf'),True,False,None,'0.5'):
            with self.subTest(value=value):
                self.assertEqual(self.call([dict(self.row,score=value)]),s.unavailable())
    def test_bad_collection_and_items(self):
        for value in (None,{},'abc',3,iter([self.row]),[None],[list(self.row)]):
            with self.subTest(value=repr(value)):
                self.assertEqual(self.call(value),s.unavailable())
    def test_one_to_three_and_tuple(self):
        for count in (1,2,3):
            self.assertEqual(self.call([self.row]*count)[0],200)
        self.assertEqual(self.call((self.row,))[1]['evidence'],[self.row])
    def test_empty(self):
        self.assertEqual(self.call([]),(200,{'ok':True,'evidence':[],'reason':'no_evidence'}))
    def test_finite_score_no_new_range_policy(self):
        for value in (-1,0,1,2):
            self.assertEqual(self.call([dict(self.row,score=value)])[0],200)
    def test_invalid_query_never_calls_either_provider(self):
        for query in ('',' ',None,3,False,[],{}):
            for mode in ('mock','adapter'):
                with self.subTest(query=query,mode=mode):
                    provider=Mock(); repo=Mock(); mock=Mock()
                    self.assertEqual(s.dispatch(query,['all'],mode=mode,adapter_enabled=True,embedder=provider,repository=repo,mock_search=mock),s.unavailable())
                    provider.assert_not_called();repo.search.assert_not_called();mock.assert_not_called()
    def test_explicit_normal_mock_preserved(self):
        expected=(200,{'ok':True,'evidence':[self.row],'reason':None})
        mock=Mock(return_value=expected)
        self.assertEqual(s.dispatch('query',['all'],mode='mock',mock_search=mock),expected)
        mock.assert_called_once_with('query',['all'],3)
    def test_repository_exception_safe(self):
        repo=Mock();repo.search.side_effect=RuntimeError('private connection details')
        result=s.search_with_adapters('q',['all'],3,lambda q,m,d:{'model':m,'embedding':[1.0]*d},repo)
        self.assertEqual(result,s.unavailable())
    def test_it_uses_validated_levels(self):
        embed=Mock();repo=Mock();mock=Mock()
        expected=(200,{'ok':True,'evidence':[],'reason':'no_evidence'})
        mock.return_value=expected
        self.assertEqual(s.dispatch('q',['all','it'],mode='mock',mock_search=mock),expected)
        mock.assert_called_once_with('q',['all','it'],3)


class LiveEmbeddingBoundaryTests(unittest.TestCase):
    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *_): self.close()

    def test_request_and_response_with_fake_transport(self):
        captured = []
        def fake_open(request, timeout):
            captured.append((request, timeout))
            return self.Response(json.dumps({'model':'text-embedding-3-large',
                'data':[{'index':0,'embedding':[1.0]*3072}]}).encode())
        with patch.dict('os.environ', {'OPENAI_API_KEY':'fake-test-only'}, clear=True):
            result=s.OpenAIEmbeddingProvider(opener=fake_open)('VPN','text-embedding-3-large',3072)
        self.assertEqual(len(result['embedding']),3072)
        request,timeout=captured[0]
        self.assertEqual(timeout,10)
        self.assertEqual(request.full_url,'https://api.openai.com/v1/embeddings')
        self.assertEqual(json.loads(request.data),{'input':'VPN','model':'text-embedding-3-large',
            'dimensions':3072,'encoding_format':'float'})

    def test_no_key_or_bad_query_never_calls_transport(self):
        opener=Mock()
        provider=s.OpenAIEmbeddingProvider(opener=opener)
        with patch.dict('os.environ', {}, clear=True):
            for query in ('', ' ', None):
                with self.assertRaises(ValueError): provider(query,'text-embedding-3-large',3072)
            with self.assertRaises(ValueError): provider('VPN','text-embedding-3-large',3072)
        opener.assert_not_called()

    def test_bad_api_result_is_503_without_details(self):
        opener=Mock(return_value=self.Response(json.dumps({'model':'text-embedding-3-large',
            'data':[{'index':0,'embedding':[1.0]}]}).encode()))
        with patch.dict('os.environ', {'OPENAI_API_KEY':'fake-test-only'}, clear=True):
            result=s.search_with_adapters('VPN',['all'],3,s.OpenAIEmbeddingProvider(opener=opener),Mock())
        self.assertEqual(result,s.unavailable())

    def test_transport_exception_is_503_without_details(self):
        opener=Mock(side_effect=RuntimeError('private diagnostics'))
        with patch.dict('os.environ', {'OPENAI_API_KEY':'fake-test-only'}, clear=True):
            result=s.search_with_adapters('VPN',['all'],3,s.OpenAIEmbeddingProvider(opener=opener),Mock())
        self.assertEqual(result,s.unavailable())
