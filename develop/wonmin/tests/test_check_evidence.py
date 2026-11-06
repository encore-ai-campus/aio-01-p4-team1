"""Evidence consistency must not turn a functional failure into a pass."""
import copy
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'tools/check-evidence.py'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SOURCE.exists(), 'evidence consistency auditor must exist')
        s = importlib.util.spec_from_file_location('evidence', SOURCE)
        self.module = importlib.util.module_from_spec(s); s.loader.exec_module(self.module)
        self.report = {'verdict':'FAIL_SCOPED_APP_VARIANTS', 'actual_llm_executions':1,
            'summary':{'n':1,'failed':1,'p50_seconds':1,'p95_seconds':1,'max_seconds':1,'method':'nearest-rank; all attempts including failures'},
            'results':[{'case':'TM-02','round':1,'passed':False,'errors':[],
                'attempts':[{'request':{'request_id':'fresh-1'},'seconds':1,'errors':['clarify_content']}],
                'traces':[{'id':1,'request_id':'fresh-1','nodes':['N06 Triage model','N06 Triage Agent'],
                           'triage':{'executed':True,'error':None}}]}]}

    def test_consistent_failure_is_preserved_as_functional_failure(self):
        result = self.module.audit_report(self.report)
        self.assertEqual(result['integrity_errors'], [])
        self.assertFalse(result['functional_passed'])
        self.assertEqual(result['failed_attempts'], 1)

    def test_forged_pass_or_percentile_is_rejected(self):
        forged = copy.deepcopy(self.report); forged['verdict']='PASS_SCOPED_APP_VARIANTS'
        self.assertIn('functional_verdict_mismatch', self.module.audit_report(forged)['integrity_errors'])
        forged = copy.deepcopy(self.report); forged['summary']['p95_seconds']=0
        self.assertIn('latency_summary_mismatch', self.module.audit_report(forged)['integrity_errors'])

    def test_reused_execution_and_round_request_key_are_rejected(self):
        forged = copy.deepcopy(self.report)
        second = copy.deepcopy(forged['results'][0]); second['round']=2
        forged['results'].append(second)
        errors = self.module.audit_report(forged)['integrity_errors']
        self.assertIn('reused_request_key_between_rounds', errors)
        self.assertIn('reused_llm_execution_id', errors)

    def test_no_actual_llm_receipt_is_incomplete_evidence(self):
        forged = copy.deepcopy(self.report); forged['results'][0]['traces'][0]['triage']['executed']=False
        self.assertIn('missing_actual_llm_execution', self.module.audit_report(forged)['integrity_errors'])

    def test_execution_flag_without_model_node_receipt_is_rejected(self):
        forged = copy.deepcopy(self.report); forged['results'][0]['traces'][0]['nodes']=[]
        self.assertIn('missing_model_node_receipt', self.module.audit_report(forged)['integrity_errors'])


if __name__=='__main__':unittest.main()
