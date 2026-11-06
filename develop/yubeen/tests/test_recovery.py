"""P1-4 Fake updates and recovery records; no real database or API."""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import rag_index as index
import rag_verify as verify


def source(text_a='## first\na\n## second\nb\n', text_b='## only\nfixed\n'):
    return {'list_response': {'docs': [{'name': k, 'access_level': 'all'} for k in ('mock-a', 'mock-b')]},
            'document_responses': {
                'mock-a': {'name': 'mock-a', 'title': 'A', 'text': text_a},
                'mock-b': {'name': 'mock-b', 'title': 'B', 'text': text_b}}}


class RecoveryUpdateTests(unittest.TestCase):
    def setUp(self):
        self.store = index.MockStore()
        self.base = source()
        self.assertEqual(self.run_index(self.base)['counts']['indexed'], 2)

    def run_index(self, data, embedder=verify.mock_embed):
        return index.index_snapshot(data, embedder, self.store)

    def check_chunks(self, key, count):
        chunks = self.store.documents[key]['chunks']
        self.assertEqual(len(chunks), count)
        self.assertEqual([c['chunk_no'] for c in chunks], list(range(count)))
        for chunk in chunks:
            self.assertEqual(chunk['content_hash'], hashlib.sha256(chunk['content'].encode()).hexdigest())
        self.assertFalse(verify.recovery_inventory(self.store)[0]['duplicate_chunk_nos'])

    def test_unchanged_and_one_document_changed(self):
        before = copy.deepcopy(self.store.documents['mock-b'])
        replacements = self.store.replacements
        self.assertEqual(self.run_index(self.base)['counts']['skipped'], 2)
        self.assertEqual(self.store.replacements, replacements)
        changed = source(text_a='## first\nchanged\n## second\nb\n')
        result = self.run_index(changed)
        self.assertEqual(result['counts'], {'indexed': 1, 'skipped': 1, 'rejected': 0, 'failed': 0})
        self.assertEqual(self.store.documents['mock-b'], before)
        self.check_chunks('mock-a', 2)
        self.assertEqual(self.run_index(changed)['counts']['skipped'], 2)

    def test_chunk_increase_decrease_and_no_stale_chunks(self):
        increased = source(text_a='## one\na\n## two\nb\n## three\nc\n')
        self.assertEqual(self.run_index(increased)['counts']['indexed'], 1)
        self.check_chunks('mock-a', 3)
        reduced = source(text_a='## only\nnew\n')
        self.assertEqual(self.run_index(reduced)['counts']['indexed'], 1)
        self.check_chunks('mock-a', 1)
        self.assertEqual(self.run_index(reduced)['counts']['skipped'], 2)

    def test_embedding_failures_preserve_and_retry(self):
        changed = source(text_a='## one\nnew\n## two\nnewer\n')
        before = copy.deepcopy(self.store.documents)
        for fail_at in (1, 2):
            calls = []
            def fail(content, model, dimensions):
                calls.append(content)
                if len(calls) == fail_at:
                    raise RuntimeError('private-upstream')
                return verify.mock_embed(content, model, dimensions)
            result = self.run_index(changed, fail)
            self.assertEqual(result['counts']['failed'], 1)
            self.assertEqual(result['counts']['skipped'], 1)
            self.assertEqual(self.store.documents, before)
        self.assertEqual(self.run_index(changed)['counts']['indexed'], 1)
        self.assertEqual(self.run_index(changed)['counts']['skipped'], 2)

    def test_storage_fault_after_delete_preserves_and_retry(self):
        before = copy.deepcopy(self.store.documents)
        changed = source(text_a='## only\nnew\n')
        self.store.fail_after_delete = True
        result = self.run_index(changed)
        self.assertEqual(result['counts']['failed'], 1)
        self.assertEqual(result['counts']['skipped'], 1)
        self.assertEqual(self.store.documents, before)
        self.store.fail_after_delete = False
        self.assertEqual(self.run_index(changed)['counts']['indexed'], 1)
        self.check_chunks('mock-a', 1)

    def test_duplicate_source_rejected_then_clean_retry(self):
        before = copy.deepcopy(self.store.documents)
        duplicate = source()
        duplicate['list_response']['docs'].append(copy.deepcopy(duplicate['list_response']['docs'][0]))
        result = self.run_index(duplicate)
        self.assertGreaterEqual(result['counts']['rejected'], 1)
        self.assertEqual(self.store.documents, before)
        self.assertEqual(self.run_index(self.base)['counts']['skipped'], 2)


class RecoveryRecordTests(unittest.TestCase):
    def test_before_after_append_and_duplicate_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / 'recovery.md'
            before = verify.recovery_record('before', 'fake-run')
            verify.append_recovery_report(path, before)
            after = verify.recovery_record('after', 'fake-run', before)
            verify.append_recovery_report(path, after)
            reports = verify.recovery_reports(path)
            self.assertEqual([r['phase'] for r in reports], ['before', 'after'])
            self.assertTrue(reports[1]['comparison']['same_inventory'])
            self.assertFalse(reports[1]['actual_restart_or_restore'])
            self.assertTrue(all(not any(d['duplicate_chunk_nos'] or d['missing_chunk_nos'] for d in r['documents']) for r in reports))
            with self.assertRaises(ValueError):
                verify.append_recovery_report(path, after)

    def test_after_requires_matching_before(self):
        with self.assertRaises(ValueError):
            verify.recovery_record('after', 'fake-run')
        with self.assertRaises(ValueError):
            verify.recovery_record('after', 'other', verify.recovery_record('before', 'fake-run'))
