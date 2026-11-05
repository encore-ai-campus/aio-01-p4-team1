"""Opt-in disposable localhost DB only. Never uses DATABASE_URL or OpenAI.

Caller creates an EMPTY database named codex_rag_test_*. This fixture mirrors
the published contract; it is not a migration and is never applied to team DBs.
"""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import rag_db
import rag_index
import rag_search
import rag_verify


@unittest.skipUnless(os.getenv('RAG_DISPOSABLE_TEST_DSN'), 'disposable PostgreSQL not configured')
class DisposablePostgresTests(unittest.TestCase):
    def test_real_index_repeat_update_rollback_permissions_and_inventory(self):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
        dsn=os.environ['RAG_DISPOSABLE_TEST_DSN']; info=conninfo_to_dict(dsn)
        if info.get('host') not in ('127.0.0.1','localhost','::1') or not info.get('dbname','').startswith('codex_rag_test_'):
            self.fail('refusing_non_disposable_database')
        with psycopg.connect(dsn,autocommit=True) as admin:
            # Refuse to change any pre-existing RAG schema, including previous test runs.
            self.assertIsNone(admin.execute("SELECT to_regnamespace('rag')").fetchone()[0])
            admin.execute('CREATE EXTENSION IF NOT EXISTS vector')
            admin.execute('CREATE SCHEMA rag')
            admin.execute('CREATE TABLE rag.documents (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,doc_key text UNIQUE NOT NULL,title text NOT NULL,access_level text NOT NULL CHECK(access_level IN (\'all\',\'it\')),source_url text,source_hash text NOT NULL,updated_at timestamptz NOT NULL)')
            admin.execute('CREATE TABLE rag.chunks (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,document_id bigint REFERENCES rag.documents(id),chunk_no integer NOT NULL,section text NOT NULL,content text NOT NULL,content_hash text NOT NULL,embedding vector(3072) NOT NULL,embedding_model text NOT NULL,metadata jsonb NOT NULL,UNIQUE(document_id,chunk_no))')
        source={'list_response':{'docs':[{'name':'public','access_level':'all'},{'name':'private','access_level':'it'}]},
            'document_responses':{key:dict(name=key,title=key,text='## s\n'+key,access_level=level)
                                  for key,level in [('public','all'),('private','it')]}}
        with psycopg.connect(dsn,autocommit=False) as db:
            store=rag_index.PostgresStore(db)
            first=rag_index.index_snapshot(source,rag_verify.mock_embed,store)
            self.assertEqual(first['counts']['indexed'],2)
            self.assertEqual(rag_index.index_snapshot(source,rag_verify.mock_embed,store)['counts']['skipped'],2)
            baseline=rag_db.snapshot(db);db.commit()
            source['document_responses']['public']['text']+='\n## more\nchanged'
            self.assertEqual(rag_index.index_snapshot(source,rag_verify.mock_embed,store)['counts']['indexed'],1)
            changed=rag_db.snapshot(db);db.commit()
            self.assertEqual(rag_db.compare(baseline,changed)['changed'],['public'])
            def fail(*args):raise RuntimeError('synthetic')
            source['document_responses']['public']['text']+='\nextra'
            self.assertEqual(rag_index.index_snapshot(source,fail,store)['counts']['failed'],1)
            after=rag_db.snapshot(db);db.commit()
            self.assertTrue(rag_db.compare(changed,after)['same_inventory'])
            # Force a real INSERT failure after DELETE within PostgresStore.replace.
            existing=store.read('public');document={k:existing[k] for k in ('doc_key','title','access_level','source_url','source_hash')}
            chunks=[dict(chunk_no=0,section=None,content='bad',content_hash='bad',embedding=[1.0]*3072,
                         embedding_model='text-embedding-3-large',metadata={})]
            with self.assertRaises(rag_index.IndexError):
                store.replace(document,chunks,expected_version=rag_index.version_token(existing))
            after=rag_db.snapshot(db);db.commit()
            self.assertTrue(rag_db.compare(changed,after)['same_inventory'])
            self.assertEqual(rag_index.index_snapshot(source,rag_verify.mock_embed,store)['counts']['indexed'],1)
            repo=rag_search.PgvectorSearchAdapter(db)
            settings=rag_index.load_settings();vector=[1.0]*3072
            self.assertEqual({e['doc'] for e in repo.search(vector,['all'],settings)},{'public'})
            self.assertEqual({e['doc'] for e in repo.search(vector,['all','it'],settings)},{'public','private'})
        # Database lifecycle and removal belong to the caller; no DROP here.
