"""Guard the independent-run measurement and its evidence, not workflow implementation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'tools/run-fresh.py'


class FreshRunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SOURCE.exists(), 'independent-run runner must exist')
        s = importlib.util.spec_from_file_location('fresh_runner', SOURCE)
        self.module = importlib.util.module_from_spec(s); s.loader.exec_module(self.module)

    def test_rounds_are_independent_but_duplicates_share_a_key_without_mutation(self):
        case = {'id': 'TM-06', 'input': {'request_id':'original', 'question':'same', 'attempt':1}, 'repeat':2}
        original = json.dumps(case)
        a = self.module.fresh_payload(case, 'long-prefix-' * 20, 1)
        b = self.module.fresh_payload(case, 'long-prefix-' * 20, 2)
        self.assertLessEqual(len(a['request_id']), 64)
        self.assertNotEqual(a['request_id'], b['request_id'])
        self.assertEqual(a, self.module.fresh_payload(case, 'long-prefix-' * 20, 1))
        self.assertEqual(json.dumps(case), original)

    def test_expectations_reject_wrong_scalar_types_and_missing_nested_values(self):
        case = {'expect': {'http_status':200, 'equals':{'ticket.duplicate':False,'route':'담당자 이관'}}}
        self.assertEqual(self.module.expectation_errors(case, {'status':200,'body':{'ticket':{'duplicate':False},'route':'담당자 이관'}}), [])
        self.assertTrue(self.module.expectation_errors(case, {'status':200,'body':{'ticket':{'duplicate':0},'route':'담당자 이관'}}))
        self.assertTrue(self.module.expectation_errors(case, {'status':200,'body':{'ticket':None,'route':'담당자 이관'}}))

    def test_percentiles_keep_failed_attempts_and_report_the_denominator(self):
        result = self.module.latency_summary([{'seconds':i, 'passed':i!=5} for i in range(1,6)])
        self.assertEqual(result, {'n':5,'failed':1,'p50_seconds':3,'p95_seconds':5,'max_seconds':5,'method':'nearest-rank; all attempts including failures'})

    def test_reports_do_not_overwrite_or_persist_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'report.json'
            with self.assertRaises(ValueError):self.module.write_new_json(p, {'bad':'synthetic-private-key-123'}, ['synthetic-private-key-123'])
            self.assertFalse(p.exists())
            self.module.write_new_json(p, {'safe':True}, [])
            with self.assertRaises(FileExistsError):self.module.write_new_json(p, {'safe':False}, [])
            self.assertEqual(json.loads(p.read_text()), {'safe':True})


if __name__ == '__main__':unittest.main()
