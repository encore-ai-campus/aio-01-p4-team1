import copy
import hashlib
import importlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
index = importlib.import_module('rag_index')
verify = importlib.import_module('rag_verify')
prepare = importlib.import_module('rag_prepare')


def snapshot(text='## 하나\n내용\n## 둘\n내용2', level='all'):
    return {'list_response': {'docs': [{'name': 'mock-doc', 'access_level': level}]},
            'document_responses': {'mock-doc': {'name': 'mock-doc', 'title': '합성 제목', 'text': text}}}


class IndexingTests(unittest.TestCase):
    def setUp(self):
        self.store = index.MockStore()
        self.source = snapshot()
        self.settings = index.load_settings()

    def run_index(self, source=None, embedder=None):
        return index.index_snapshot(source or self.source, embedder or verify.mock_embed, self.store, self.settings)

    def test_first_and_repeat_are_idempotent(self):
        self.assertEqual(self.run_index()['counts']['indexed'], 1)
        before = copy.deepcopy(self.store.documents)
        with patch.object(verify, 'mock_embed', side_effect=AssertionError('must not embed')):
            result = self.run_index()
        self.assertEqual(result['counts']['skipped'], 1)
        self.assertEqual(self.store.documents, before)
        self.assertEqual(self.store.replacements, 1)

    def test_reuses_exact_p0_content_and_hash(self):
        observed = []
        def embedding(content, model, dimensions):
            observed.append(content)
            return verify.mock_embed(content, model, dimensions)
        self.run_index(embedder=embedding)
        expected = prepare.chunk_document('mock-doc', '합성 제목', self.source['document_responses']['mock-doc']['text'], 'all', 'section')['chunks']
        actual = self.store.documents['mock-doc']['chunks']
        self.assertEqual(observed, [c['content'] for c in expected])
        for left, right in zip(actual, expected):
            self.assertEqual(left['content_hash'], right['content_hash'])
            self.assertEqual(left['metadata']['source_range'], right['metadata']['source_range'])
            self.assertEqual(left['document_id'], self.store.documents['mock-doc']['id'])
            self.assertEqual(len(left['embedding']), 3072)

    def test_changed_body_replaces_chunks_preserves_id(self):
        self.run_index()
        old_id = self.store.documents['mock-doc']['id']
        changed = snapshot('## 하나\n변경된 내용')
        self.assertEqual(self.run_index(changed)['counts']['indexed'], 1)
        doc = self.store.documents['mock-doc']
        self.assertEqual(doc['id'], old_id)
        self.assertEqual(len(doc['chunks']), 1)
        self.assertEqual(doc['chunks'][0]['chunk_no'], 0)

    def test_title_and_permission_changes_not_skipped(self):
        self.run_index(snapshot(level='it'))
        changed = snapshot(level='all')
        changed['document_responses']['mock-doc']['title'] = '변경 제목'
        self.assertEqual(self.run_index(changed)['counts']['indexed'], 1)
        self.assertEqual(self.store.documents['mock-doc']['access_level'], 'all')

    def test_settings_fingerprint_detects_drift(self):
        self.run_index()
        self.store.documents['mock-doc']['chunks'][0]['metadata']['index_settings_hash'] = 'old'
        self.assertEqual(self.run_index()['counts']['indexed'], 1)

    def test_permission_missing_duplicate_and_empty_rejected(self):
        for source in [snapshot(level=None), snapshot(text=' '), snapshot()]:
            if source['list_response']['docs'][0]['access_level'] == 'all' and source['document_responses']['mock-doc']['text'].strip():
                source['list_response']['docs'] *= 2
            result = self.run_index(source)
            self.assertGreater(result['counts']['rejected'], 0)
        self.assertEqual(self.store.documents, {})

    def test_partial_and_rejected_leave_previous_untouched(self):
        self.run_index()
        previous = copy.deepcopy(self.store.documents)
        for text in ['## good\nok\n## long\n'+'가'*3000, '## long\n'+'가'*3000]:
            with patch.object(verify, 'mock_embed', side_effect=AssertionError('must not embed')):
                result = self.run_index(snapshot(text))
            self.assertEqual(result['counts']['rejected'], 1)
            self.assertEqual(self.store.documents, previous)

    def test_embedding_failure_after_first_chunk_preserves_previous(self):
        self.run_index()
        previous = copy.deepcopy(self.store.documents)
        calls = []
        def fail(content, model, dimensions):
            calls.append(content)
            if len(calls) == 2:
                raise RuntimeError('upstream private details')
            return verify.mock_embed(content, model, dimensions)
        result = self.run_index(snapshot('## a\n변경\n## b\n변경2'), fail)
        self.assertEqual(result['counts']['failed'], 1)
        self.assertEqual(self.store.documents, previous)
        self.assertNotIn('private', json.dumps(result))

    def test_storage_failure_rolls_back_then_retry_succeeds(self):
        self.run_index()
        previous = copy.deepcopy(self.store.documents)
        self.store.fail_after_delete = True
        changed = snapshot('## 변경\n새 내용')
        self.assertEqual(self.run_index(changed)['counts']['failed'], 1)
        self.assertEqual(self.store.documents, previous)
        self.store.fail_after_delete = False
        self.assertEqual(self.run_index(changed)['counts']['indexed'], 1)

    def test_all_embeddings_prepared_before_replace(self):
        calls = []
        def embed(content, model, dimensions):
            self.assertEqual(self.store.replacements, 0)
            calls.append(content)
            return verify.mock_embed(content, model, dimensions)
        self.run_index(embedder=embed)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.store.replacements, 1)

    def test_vector_validation(self):
        base = verify.mock_embed('x', 'text-embedding-3-large', 3072)
        for vector in [[], [1.0]*3071, [0.0]*3072, [math.nan]+[1.0]*3071,
                       [math.inf]+[1.0]*3071, [True]+[1.0]*3071, ['secret']+[1.0]*3071]:
            with self.subTest(vector_type=type(vector[0]).__name__ if vector else 'empty'):
                with self.assertRaises(index.IndexError):
                    index.validate_embedding(dict(base, embedding=vector), self.settings)
        with self.assertRaises(index.IndexError):
            index.validate_embedding(dict(base, model='other'), self.settings)

    def test_invalid_vector_prevents_any_storage(self):
        result = self.run_index(embedder=lambda *args: {'model':'text-embedding-3-large','embedding':[0.0]*3072})
        self.assertEqual(result['counts']['failed'],1)
        self.assertEqual(self.store.replacements,0)

    def test_permission_reduction_suspends_public_chunks(self):
        self.run_index()
        result = self.run_index(snapshot(level='it'))
        self.assertEqual(result['counts']['rejected'], 1)
        self.assertIn('mock-doc', self.store.suspended)
        self.assertEqual(self.store.documents['mock-doc']['chunks'], [])
        self.assertEqual(self.store.documents['mock-doc']['access_level'], 'it')

    def test_permission_reduction_with_oversized_body_still_suspends(self):
        self.run_index()
        result = self.run_index(snapshot('## long\n'+'가'*3000, level='it'))
        self.assertEqual(result['counts']['rejected'], 1)
        self.assertEqual(self.store.documents['mock-doc']['chunks'], [])
        self.assertEqual(self.store.documents['mock-doc']['access_level'], 'it')

    def test_injected_settings_cannot_change_common_contract(self):
        for key, value in [('chunking','300'),('embedding_dimensions',10),('overlap',1)]:
            with self.assertRaises(index.IndexError):
                index.index_snapshot(self.source,verify.mock_embed,self.store,dict(self.settings, **{key:value}))

    def test_safe_summary_contains_no_source_or_credential(self):
        source = snapshot('## restricted-heading\nrestricted-body', 'it')
        source['document_responses']['mock-doc']['title'] = 'restricted-title'
        result = self.run_index(source)
        rendered = json.dumps(result)
        for value in ['restricted-heading', 'restricted-body', 'restricted-title', 'embedding']:
            self.assertNotIn(value, rendered)

    def test_masked_snapshot_is_not_source(self):
        with self.assertRaises(index.IndexError):
            self.run_index({'mode':'api','prepared_rows':[]})

    def test_document_failure_does_not_stop_other_documents(self):
        source = snapshot()
        source['list_response']['docs'].append({'name':'second','access_level':'it'})
        source['document_responses']['second'] = {'name':'second','title':'safe','text':'## one\nsecond-body'}
        def embed(content, model, dimensions):
            if 'second-body' in content:
                raise RuntimeError('synthetic fault')
            return verify.mock_embed(content, model, dimensions)
        result = self.run_index(source, embed)
        self.assertEqual(result['counts']['indexed'], 1)
        self.assertEqual(result['counts']['failed'], 1)


class PostgresAdapterTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.connection.autocommit = False
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.cursor.fetchone.side_effect = [None, (7,)]
        self.adapter = index.PostgresStore(self.connection)
        self.doc = {'doc_key':'safe-key', 'title':"title'; DROP TABLE ignored",'access_level':'all','source_url':'/docs/safe-key','source_hash':'hash'}
        self.chunk = prepare.chunk_document('safe-key','title','## one\nbody','all','section')['chunks'][0]
        self.chunk.update(embedding=[1.0]*3072, embedding_model='text-embedding-3-large')

    def test_single_connection_transaction_and_bound_parameters(self):
        self.adapter.replace(self.doc,[self.chunk])
        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()
        calls=self.cursor.execute.call_args_list
        self.assertEqual(len(calls),5)
        self.assertIn('pg_advisory_xact_lock', calls[0].args[0])
        self.assertTrue(calls[3].args[0].startswith('DELETE FROM rag.chunks'))
        for call in calls:
            self.assertNotIn(self.doc['title'],call.args[0])
            self.assertNotIn('CREATE ',call.args[0])
        self.assertEqual(calls[4].args[1][0],7)

    def test_failure_after_delete_rolls_back(self):
        self.cursor.execute.side_effect=[None,None,None,None,RuntimeError('private SQL details')]
        with self.assertRaisesRegex(index.IndexError,'^storage_replace_failed$'):
            self.adapter.replace(self.doc,[self.chunk])
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()

    def test_autocommit_rejected(self):
        self.connection.autocommit=True
        with self.assertRaises(index.IndexError):
            index.PostgresStore(self.connection)

    def test_read_maps_existing_schema_without_extra_columns(self):
        self.cursor.fetchone.side_effect = None
        self.cursor.fetchone.return_value=(7,'safe-key','title','all','/docs/safe-key','hash','timestamp')
        self.cursor.fetchall.return_value=[(0,'chash','text-embedding-3-large',{'index_settings_hash':'settings'},3072)]
        state=self.adapter.read('safe-key')
        self.assertEqual(state['chunks'][0]['dimensions'],3072)
        self.assertEqual(state['id'],7)


class IndexCliWorkflowTests(unittest.TestCase):
    def test_mock_scenario_passes(self):
        result=verify.verify_mock()
        self.assertTrue(result['ok'])
        self.assertEqual(result['first'],{'indexed':4,'skipped':0,'rejected':1,'failed':0})
        self.assertEqual(result['second']['skipped'],4)

    def test_real_mode_is_blocked_without_calls(self):
        with redirect_stderr(io.StringIO()), patch.object(verify,'verify_mock') as run:
            with self.assertRaises(SystemExit) as caught:
                verify.main(['index','--source','api','--scenario','initial-and-repeat','--json'])
            self.assertEqual(caught.exception.code,2)
            run.assert_not_called()

    def test_report_appends_without_destroying_history(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as directory:
            output=Path(directory)/'index.md'
            output.write_text('previous-history\n')
            with redirect_stdout(io.StringIO()):
                verify.main(['index','--scenario','initial-and-repeat','--output',str(output)])
            self.assertTrue(output.read_text().startswith('previous-history\n'))
            self.assertIn('"ok": true',output.read_text())

    def test_workflow_is_inactive_fixed_command_and_safe_graph(self):
        workflow=json.loads((ROOT/'workflows/oke-index.json').read_text())
        self.assertFalse(workflow['active'])
        nodes={node['name']:node for node in workflow['nodes']}
        for name, outputs in workflow['connections'].items():
            self.assertIn(name,nodes)
            for branch in outputs['main']:
                for connection in branch:
                    self.assertIn(connection['node'],nodes)
        command=next(n for n in nodes.values() if n['type']=='n8n-nodes-base.executeCommand')['parameters']['command']
        self.assertEqual(command,'python3 /opt/oke-rag/tools/rag_verify.py index --source mock --scenario initial-and-repeat --json')
        self.assertNotIn('{{',command)
        self.assertEqual(workflow['settings']['saveDataSuccessExecution'],'none')


class SafetyDefectRegressionTests(unittest.TestCase):
    def setUp(self):
        self.store = index.MockStore()
        self.source = snapshot()
        index.index_snapshot(self.source, verify.mock_embed, self.store)

    def test_reduction_with_empty_body_and_bad_title(self):
        for field, value in [('text', ''), ('text', ' '), ('title', None)]:
            with self.subTest(field=field, value=value):
                store = index.MockStore()
                index.index_snapshot(snapshot(), verify.mock_embed, store)
                old_id = store.documents['mock-doc']['id']
                changed = snapshot(level='it')
                changed['document_responses']['mock-doc'][field] = value
                result = index.index_snapshot(changed, verify.mock_embed, store)
                self.assertEqual(result['counts']['rejected'], 1)
                self.assertEqual(store.documents['mock-doc']['id'], old_id)
                self.assertEqual(store.documents['mock-doc']['chunks'], [])
                self.assertEqual(store.documents['mock-doc']['access_level'], 'it')

    def test_unknown_conflicting_permission_does_not_mutate_existing(self):
        previous = copy.deepcopy(self.store.documents)
        changed = snapshot(level='it')
        changed['document_responses']['mock-doc']['access_level'] = 'all'
        result = index.index_snapshot(changed, verify.mock_embed, self.store)
        self.assertEqual(result['counts']['rejected'], 1)
        self.assertEqual(self.store.documents, previous)
        changed = snapshot(level=None)
        changed['document_responses']['mock-doc']['name'] = 'different-document'
        changed['document_responses']['mock-doc']['access_level'] = 'it'
        index.index_snapshot(changed, verify.mock_embed, self.store)
        self.assertEqual(self.store.documents, previous)

    def test_suspension_failure_is_failed_not_rejected(self):
        with patch.object(self.store, 'suspend', side_effect=RuntimeError('private-key-example')):
            result = index.index_snapshot(snapshot(level='it'), verify.mock_embed, self.store)
        self.assertEqual(result['counts']['failed'], 1)
        self.assertEqual(result['counts']['rejected'], 0)
        self.assertEqual(result['documents'][0]['reason'], 'permission_suspension_failed')
        self.assertNotIn('private-key-example', json.dumps(result))

    def test_suspended_identity_and_state_survive_repeat(self):
        old_id = self.store.documents['mock-doc']['id']
        index.index_snapshot(snapshot(level='it'), verify.mock_embed, self.store)
        for level in ('it', 'all'):
            result = index.index_snapshot(snapshot(level=level), verify.mock_embed, self.store)
            self.assertEqual(result['counts']['rejected'], 1)
            self.assertEqual(result['documents'][0]['reason'], 'index_suspended_requires_review')
            self.assertEqual(self.store.documents['mock-doc']['id'], old_id)
            self.assertEqual(self.store.documents['mock-doc']['chunks'], [])

    def test_concurrent_permission_change_cannot_republish_all(self):
        changed = snapshot('## 새 절\n새 내용')
        def embed(content, model, dimensions):
            self.store.suspend('mock-doc')
            return verify.mock_embed(content, model, dimensions)
        result = index.index_snapshot(changed, embed, self.store)
        self.assertEqual(result['counts']['failed'], 1)
        self.assertEqual(result['documents'][0]['reason'], 'stale_document_version')
        self.assertEqual(self.store.documents['mock-doc']['access_level'], 'it')
        self.assertEqual(self.store.documents['mock-doc']['chunks'], [])

    def test_concurrent_version_change_is_not_overwritten(self):
        changed = snapshot('## 새 절\n새 내용')
        def embed(content, model, dimensions):
            self.store.documents['mock-doc']['updated_at'] = 'another-writer-version'
            return verify.mock_embed(content, model, dimensions)
        result = index.index_snapshot(changed, embed, self.store)
        self.assertEqual(result['documents'][0]['reason'], 'stale_document_version')
        self.assertEqual(self.store.documents['mock-doc']['updated_at'], 'another-writer-version')

    def test_two_thread_interleaving_compare_and_swap(self):
        import threading
        prepared = threading.Event()
        changed = threading.Event()
        results = []
        def embed(content, model, dimensions):
            prepared.set()
            if not changed.wait(3):
                raise RuntimeError('synchronization_timeout')
            return verify.mock_embed(content, model, dimensions)
        def worker():
            results.append(index.index_snapshot(snapshot('## new\nnew body'), embed, self.store))
        worker_thread = threading.Thread(target=worker)
        worker_thread.start()
        self.assertTrue(prepared.wait(3))
        self.store.suspend('mock-doc')
        changed.set()
        worker_thread.join(3)
        self.assertFalse(worker_thread.is_alive())
        self.assertEqual(results[0]['documents'][0]['reason'], 'stale_document_version')
        self.assertEqual(self.store.documents['mock-doc']['chunks'], [])

    def test_total_embedding_outage_returns_false_and_exit_one(self):
        with patch.object(verify, 'mock_embed', side_effect=RuntimeError('private upstream exception')):
            result = verify.verify_mock()
            self.assertFalse(result['ok'])
            self.assertEqual(result['first']['failed'], 4)
            self.assertFalse(result['checks']['expected_first_counts'])
            self.assertFalse(result['checks']['fault_scenarios_executed'])
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    verify.main(['index', '--scenario', 'initial-and-repeat', '--json'])
            self.assertEqual(caught.exception.code, 1)
            self.assertFalse(json.loads(out.getvalue())['ok'])
            self.assertNotIn('private upstream exception', out.getvalue()+err.getvalue())

    def test_empty_fixture_does_not_vacuously_pass(self):
        result = verify.verify_mock({'list_response': {'docs': []}, 'document_responses': {}})
        self.assertFalse(result['ok'])
        self.assertFalse(result['checks']['stored_documents_present'])
        self.assertFalse(result['checks']['fk_and_unique_valid'])
        self.assertFalse(result['checks']['embedding_failure_preserves_previous'])


class TransactionFailureRegressionTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.connection.autocommit = False
        self.connection.closed = False
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.adapter = index.PostgresStore(self.connection)
        self.doc = {'doc_key':'x','title':'title','access_level':'all','source_url':'/docs/x','source_hash':'hash'}
        self.chunk = prepare.chunk_document('x','title','body','all','section')['chunks'][0]
        self.chunk.update(embedding=[1.0]*3072, embedding_model='text-embedding-3-large')

    def test_rollback_failure_is_sanitized_and_connection_discarded(self):
        self.cursor.execute.side_effect = RuntimeError('secret-query')
        self.connection.rollback.side_effect = RuntimeError('secret-rollback')
        with self.assertRaisesRegex(index.IndexError, '^storage_rollback_failed$'):
            self.adapter.replace(self.doc, [self.chunk])
        self.connection.close.assert_called_once()
        with self.assertRaisesRegex(index.IndexError, '^storage_connection_unusable$'):
            self.adapter.read('x')
        self.assertEqual(self.connection.cursor.call_count, 1)

    def test_commit_unknown_discards_even_if_close_fails(self):
        self.cursor.fetchone.side_effect = [None, (7,)]
        self.connection.commit.side_effect = RuntimeError('secret commit ACK lost')
        self.connection.close.side_effect = RuntimeError('secret close failure')
        with self.assertRaisesRegex(index.IndexError, '^storage_commit_unknown$'):
            self.adapter.replace(self.doc, [self.chunk])
        self.connection.rollback.assert_not_called()
        self.assertFalse(self.adapter.usable)
        with self.assertRaisesRegex(index.IndexError, '^storage_connection_unusable$'):
            self.adapter.suspend('x')

    def test_sql_failure_rollback_success_has_fixed_error(self):
        self.cursor.execute.side_effect = RuntimeError('secret SQL values')
        with self.assertRaisesRegex(index.IndexError, '^storage_replace_failed$'):
            self.adapter.replace(self.doc, [self.chunk])
        self.connection.rollback.assert_called_once()
        self.assertTrue(self.adapter.usable)

    def test_connection_sqlstate_failure_is_not_reused(self):
        class Disconnected(Exception):
            sqlstate = '08006'
        self.cursor.execute.side_effect = Disconnected('secret DSN')
        with self.assertRaisesRegex(index.IndexError, '^storage_connection_unusable$'):
            self.adapter.read('x')
        self.connection.close.assert_called_once()

    def test_locked_version_check_precedes_every_mutation(self):
        self.cursor.fetchone.return_value = (7,'x','title','it','/docs/x','hash','new-version')
        self.cursor.fetchall.return_value = []
        with self.assertRaisesRegex(index.IndexError, '^stale_document_version$'):
            self.adapter.replace(self.doc, [self.chunk], expected_version='stale-version')
        queries = [c.args[0] for c in self.cursor.execute.call_args_list]
        self.assertIn('pg_advisory_xact_lock', queries[0])
        self.assertIn('FOR UPDATE', queries[1])
        self.assertFalse(any(q.startswith(('INSERT','UPDATE','DELETE')) for q in queries))
        self.connection.rollback.assert_called_once()

    def test_insert_race_does_not_upsert_over_existing_document(self):
        self.cursor.fetchone.side_effect = [None, None]
        with self.assertRaisesRegex(index.IndexError, '^stale_document_version$'):
            self.adapter.replace(self.doc,[self.chunk])
        insert_query = self.cursor.execute.call_args_list[2].args[0]
        self.assertIn('ON CONFLICT (doc_key) DO NOTHING', insert_query)
        self.assertNotIn('DO UPDATE', insert_query)

    def test_suspend_retains_row_changes_permission_and_deletes_chunks(self):
        self.cursor.fetchone.return_value = (7,)
        self.adapter.suspend('x')
        queries = self.cursor.execute.call_args_list
        self.assertIn('pg_advisory_xact_lock', queries[0].args[0])
        self.assertIn('FOR UPDATE', queries[1].args[0])
        self.assertEqual(queries[2].args[1], ('it',7))
        self.assertTrue(queries[3].args[0].startswith('DELETE FROM rag.chunks'))
        self.assertFalse(any('DELETE FROM rag.documents' in q.args[0] for q in queries))
        self.connection.commit.assert_called_once()


class AdditionalTransactionTests(unittest.TestCase):
    def test_existing_row_update_under_lock_preserves_id_and_binding(self):
        connection = MagicMock()
        connection.autocommit = False
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (7, 'x', 'old', 'all', '/docs/x', 'oldhash', 'timestamp')
        cursor.fetchall.return_value = [(0, 'oldchunk', 'text-embedding-3-large', {}, 3072)]
        adapter = index.PostgresStore(connection)
        current = adapter.read('x')
        connection.reset_mock()
        document = {'doc_key':'x','title':'new-title','access_level':'all','source_url':'/docs/x','source_hash':'newhash'}
        chunk = prepare.chunk_document('x','new-title','new body','all','section')['chunks'][0]
        chunk.update(embedding=[1.0]*3072,embedding_model='text-embedding-3-large')
        adapter.replace(document,[chunk],expected_version=index.version_token(current))
        calls = cursor.execute.call_args_list
        update = next(c for c in calls if c.args[0].startswith('UPDATE rag.documents'))
        self.assertEqual(update.args[1][-1],7)
        self.assertNotIn('new-title',update.args[0])
        self.assertFalse(any(c.args[0].startswith('INSERT INTO rag.documents') for c in calls))
        connection.commit.assert_called_once()

    def test_read_commit_unknown_invalidates_connection(self):
        connection = MagicMock()
        connection.autocommit = False
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = None
        connection.commit.side_effect = RuntimeError('private ACK lost')
        adapter = index.PostgresStore(connection)
        with self.assertRaisesRegex(index.IndexError,'^storage_commit_unknown$'):
            adapter.read('x')
        self.assertFalse(adapter.usable)
        connection.close.assert_called_once()

    def test_engine_reports_unknown_storage_outcome_without_success(self):
        store = index.MockStore()
        with patch.object(store,'replace',side_effect=index.IndexError('storage_commit_unknown')):
            result = index.index_snapshot(snapshot(),verify.mock_embed,store)
        self.assertEqual(result['counts']['indexed'],0)
        self.assertEqual(result['counts']['failed'],1)
        self.assertEqual(result['documents'][0]['reason'],'storage_commit_unknown')


if __name__ == '__main__':
    unittest.main()
