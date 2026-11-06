import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("period7_curl_qa", ROOT / "tools/period7-curl-qa.py")
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)


class Period7CurlQaTests(unittest.TestCase):
    def test_transport_classification_separates_tls_timeout_and_network(self):
        self.assertEqual(qa.curl_transport_kind(28), "timeout")
        self.assertEqual(qa.curl_transport_kind(60), "tls")
        self.assertEqual(qa.curl_transport_kind(7), "network_or_curl_error")

    def test_unexpected_forbidden_missing_route_or_transport_failure_aborts(self):
        self.assertTrue(qa.is_baseline_access_failure(403))
        self.assertTrue(qa.is_baseline_access_failure(404))
        self.assertTrue(qa.is_baseline_access_failure(0))
        self.assertFalse(qa.is_baseline_access_failure(200))
        self.assertFalse(qa.is_baseline_access_failure(400))

    def test_report_path_must_be_new_json_under_owned_runs(self):
        with self.assertRaises(qa.NotRunnable):
            qa.validate_output_path(Path("/tmp/period7-outside.json"))
        with self.assertRaises(qa.NotRunnable):
            qa.validate_output_path(ROOT / "cases/team.json")

    def test_http_200_requires_matching_request_id(self):
        report = qa.safe_summary("WF-01", "expected-id", 200,
            {"request_id": "different-id", "route": "자동 답변", "sources": [], "ticket": None}, 0.2,
            {"expect": {"http_status": 200, "route": "자동 답변", "ticket": None}}, 1)
        self.assertFalse(report["checks"]["request_id_matches"])
        self.assertEqual(report["verdict"], "FAIL_OR_INCOMPLETE")

    def test_http_400_codes_do_not_require_request_id_echo(self):
        report = qa.safe_summary("WF-13-empty", "generated-id", 400,
            {"codes": ["question_required"]}, 0.1,
            {"expect": {"http_status": 400, "code": "question_required"}}, 1)
        self.assertIsNone(report["observed"]["request_id_matches"])
        self.assertNotIn("request_id_matches", report["checks"])
        self.assertTrue(report["checks"]["error_code"])

    def test_http_400_is_not_accepted_as_wf08_injection_success(self):
        report = qa.safe_summary("WF-08", "generated-id", 400,
            {"codes": ["blocked"]}, 0.1,
            {"expect": {"http_status": 200, "route_if_200": "차단", "ticket": None}}, 1)
        self.assertEqual(report["verdict"], "FAIL_OR_INCOMPLETE")

    def test_case_level_unobserved_requirements_prevent_pass(self):
        report = qa.safe_summary("WF-01", "id-1", 200,
            {"request_id": "id-1", "route": "자동 답변", "sources": [{"doc": "remote-work-vpn"}], "ticket": None},
            0.2, {"expect": {"http_status": 200, "route": "자동 답변", "source_doc": "remote-work-vpn", "ticket": None},
                  "unobserved_for_full_pass": ["verifier trace"]}, 1)
        self.assertEqual(report["verdict"], "PARTIAL_UNOBSERVED")
        self.assertIn("verifier trace", report["unobserved"])

    def test_sensitive_and_db_flags_are_checked_or_marked_unobserved(self):
        masked = qa.safe_summary("WF-07", "id-2", 200,
            {"request_id": "id-2", "route": "자동 답변", "answer": "010-****-2135", "security": {"masked": 1}},
            0.2, {"expect": {"http_status": 200, "masked_contact": True}}, 1)
        self.assertTrue(masked["checks"]["masked_count"])
        self.assertTrue(masked["checks"]["answer_has_mask_token"])
        duplicate = qa.safe_summary("WF-09", "id-3", 200,
            {"request_id": "id-3", "route": "담당자 이관", "ticket": {"ticket_id": "T-9001"}}, 0.2,
            {"expect": {"http_status": 200, "ticket_required": True, "only_one_ticket": True}}, 1)
        self.assertEqual(duplicate["verdict"], "PARTIAL_UNOBSERVED")
        self.assertTrue(any("DB observation" in item for item in duplicate["unobserved"]))

    def test_permission_text_check_remains_partial_without_full_document_trace(self):
        report = qa.safe_summary("TM-11", "id-4", 200,
            {"request_id": "id-4", "route": "권한 없음", "sources": [], "ticket": None}, 0.2,
            {"expect": {"http_status": 200, "route_in": ["권한 없음", "담당자 이관"],
                         "no_it_source_or_text": True}}, 1)
        self.assertTrue(report["checks"]["no_it_source_reference"])
        self.assertEqual(report["verdict"], "PARTIAL_UNOBSERVED")

    def test_denied_route_must_not_have_ticket_and_handoff_route_requires_one(self):
        denied = qa.safe_summary("WF-05", "id-6", 200,
            {"request_id": "id-6", "route": "권한 없음", "ticket": None, "sources": []}, 0.2,
            {"expect": {"http_status": 200, "ticket_required_if_handoff": True}}, 1)
        handoff_missing_ticket = qa.safe_summary("WF-05", "id-7", 200,
            {"request_id": "id-7", "route": "담당자 이관", "ticket": None, "sources": []}, 0.2,
            {"expect": {"http_status": 200, "ticket_required_if_handoff": True}}, 1)
        self.assertTrue(denied["checks"]["handoff_ticket_present"])
        self.assertFalse(handoff_missing_ticket["checks"]["handoff_ticket_present"])

    def test_unexpected_response_text_is_not_copied_into_safe_report(self):
        marker = "private-raw-response-marker"
        report = qa.safe_summary("WF-01", "id-5", 200,
            {"request_id": "id-5", "route": marker, "reason": marker,
             "sources": [{"doc": marker}], "ticket": {"ticket_id": marker}}, 0.2,
            {"expect": {"http_status": 200}}, 1)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn(marker, serialized)
        self.assertEqual(report["observed"]["route"], "unclassified_route")
        self.assertEqual(report["observed"]["reason"], "unclassified_reason")

    def test_team_five_contains_executable_inputs_for_each_category(self):
        suite = json.loads((ROOT / "cases/period7-derived.json").read_text(encoding="utf-8"))
        categories = suite["team_five_categories"]
        self.assertEqual(len(categories), 5)
        self.assertTrue(all(category["cases"] and all("input" in case and "expect" in case
                                                       for case in category["cases"])
                            for category in categories))
        self.assertEqual({case["id"] for case in categories[3]["cases"]}, {"TM-11", "TM-12"})


if __name__ == "__main__":
    unittest.main()
