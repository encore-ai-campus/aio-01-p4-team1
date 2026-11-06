import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import rag_index
import rag_load
import rag_prepare
from rag_verify import mock_embed


class LoadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.docs = self.root / 'docs'
        self.docs.mkdir()
        self.manifest = self.root / 'permissions.json'
        self.levels = {key: 'it' if key == 'security-incident' else 'all' for key in rag_prepare.EXPECTED}
        self.write_docs()

    def write_docs(self):
        entries = {}
        for key in rag_prepare.EXPECTED:
            path = self.docs / (key + '.md')
            if not path.exists():
                path.write_text('# ' + key + '\n## 안내\n합성 안내입니다.\n')
            entries[key] = {'access_level': self.levels[key], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        self.manifest.write_text(json.dumps({'approval_status': 'approved', 'documents': entries}))

    def run_load(self, store, embed=mock_embed):
        return rag_load.run_index(self.docs, self.manifest, store=store, embedder=embed)

    def test_initial_repeat_change_and_permission(self):
        store = rag_index.MockStore()
        self.assertEqual(self.run_load(store)['counts']['indexed'], 8)
        self.assertEqual(self.run_load(store)['counts']['skipped'], 8)
        self.assertEqual(store.documents['security-incident']['access_level'], 'it')
        (self.docs / 'privacy.md').write_text('# privacy\n## 안내\n변경된 합성 안내입니다.\n')
        self.write_docs()
        result = self.run_load(store)
        self.assertEqual(result['counts']['indexed'], 1)
        self.assertEqual(result['counts']['skipped'], 7)

    def test_unapproved_or_changed_source_never_calls_embedder(self):
        def fail(*_):
            self.fail('embedding called')
        manifest = json.loads(self.manifest.read_text())
        manifest['documents']['privacy']['access_level'] = 'pending'
        self.manifest.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(rag_load.LoadError, 'permissions_unconfirmed'):
            self.run_load(rag_index.MockStore(), fail)
        self.write_docs()
        (self.docs / 'privacy.md').write_text('changed')
        with self.assertRaisesRegex(rag_load.LoadError, 'document_hash_mismatch'):
            self.run_load(rag_index.MockStore(), fail)

    def test_embedding_and_store_failure_preserve_previous_then_retry(self):
        store = rag_index.MockStore()
        self.run_load(store)
        before = store.read('privacy')
        (self.docs / 'privacy.md').write_text('# privacy\n## 안내\n새 합성 본문\n')
        self.write_docs()
        def fail(*_):
            raise ValueError('secret should not leak')
        result = self.run_load(store, fail)
        self.assertEqual(result['counts']['failed'], 1)
        self.assertEqual(store.read('privacy'), before)
        store.fail_after_delete = True
        result = self.run_load(store)
        self.assertEqual(result['counts']['failed'], 1)
        self.assertEqual(store.read('privacy'), before)
        store.fail_after_delete = False
        self.assertEqual(self.run_load(store)['counts']['indexed'], 1)
        self.assertEqual(self.run_load(store)['counts']['skipped'], 8)

    def test_real_mode_requires_explicit_gate(self):
        with self.assertRaisesRegex(rag_load.LoadError, 'real_execution_not_authorized'):
            rag_load.execute(self.docs, self.manifest, mode='real')

    def test_duplicate_approval_keys_rejected_before_services(self):
        self.manifest.write_text('{"approval_status":"approved","approval_status":"approved","documents":{}}')
        with self.assertRaisesRegex(rag_load.LoadError,'invalid_permissions_manifest'):
            self.run_load(rag_index.MockStore())


if __name__ == '__main__':
    unittest.main()
