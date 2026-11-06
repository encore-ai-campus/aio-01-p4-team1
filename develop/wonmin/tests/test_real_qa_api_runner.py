import importlib.util
import json
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "tools/real-qa-api-runner.py"
spec = importlib.util.spec_from_file_location("real_qa_api_runner", SOURCE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RealQaApiRunnerTests(unittest.TestCase):
    def test_approved_origin_only(self):
        self.assertEqual(runner.validate_base("https://aio-t1.isitsoft.kr/"), runner.DEFAULT_BASE)
        for value in (
            "http://aio-t1.isitsoft.kr",
            "https://aio-t1.isitsoft.kr:5678",
            "https://aio-t1.isitsoft.kr/path",
            "https://user:password@aio-t1.isitsoft.kr",
            "https://aio-t1.isitsoft.kr/?token=secret",
            "https://example.org",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner.validate_base(value)

    def test_ticket_lookup_requires_exactly_one_match(self):
        ticket = {"id": 31, "request_id": "qa-1", "ticket_id": "T-2001"}
        self.assertEqual(runner.ticket_for_request([ticket], "qa-1", 200), ticket)
        with self.assertRaises(runner.SafeHttpError):
            runner.ticket_for_request([], "qa-1", 200)
        with self.assertRaises(runner.SafeHttpError):
            runner.ticket_for_request([ticket, ticket], "qa-1", 200)

    def test_curl_keeps_https_stdin_secrets_and_cookie_file_private(self):
        secret = "login-password-secret"

        def fake_run(args, **kwargs):
            Path(args[args.index("--output") + 1]).write_text('{"ok":true}', encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="200", stderr="")

        secrets = {"OKE_REAL_QA_EMPLOYEE_PASSWORD": secret,
                   "OKE_REAL_QA_ADMIN_PASSWORD": "other-secret"}
        with patch.dict(runner.os.environ, secrets), patch.object(runner.subprocess, "run", side_effect=fake_run) as run:
            client = runner.Client(runner.DEFAULT_BASE)
            try:
                status, body = client.request("POST", "/api/auth/login", {"password": secret}, {200})
                args = run.call_args.args[0]
                kwargs = run.call_args.kwargs
                self.assertEqual((status, body), (200, {"ok": True}))
                self.assertIn("--proto", args)
                self.assertIn("=https", args)
                self.assertIn("--tlsv1.2", args)
                self.assertNotIn("--insecure", args)
                self.assertNotIn(secret, args)
                self.assertIn(secret, kwargs["input"])
                self.assertNotIn("OKE_REAL_QA_EMPLOYEE_PASSWORD", kwargs["env"])
                self.assertNotIn("OKE_REAL_QA_ADMIN_PASSWORD", kwargs["env"])
                self.assertEqual(stat.S_IMODE(Path(args[args.index("--cookie-jar") + 1]).stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE(Path(args[args.index("--output") + 1]).stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE(Path(client._private.name).stat().st_mode), 0o700)
            finally:
                client.close()

    def test_mocked_curl_tls_http_and_timeout_failures_remain_distinct(self):
        client = runner.Client(runner.DEFAULT_BASE)
        try:
            cases = (
                (SimpleNamespace(returncode=60, stdout="", stderr="SSL certificate verify failed"),
                 "tls_transport_error", None),
                (SimpleNamespace(returncode=28, stdout="", stderr="Operation timed out"),
                 "transport_timeout", None),
                (SimpleNamespace(returncode=7, stdout="", stderr="Connection refused"),
                 "network_transport_error", None),
            )
            for result, kind, status in cases:
                with self.subTest(kind=kind), patch.object(runner.subprocess, "run", return_value=result):
                    with self.assertRaises(runner.SafeHttpError) as caught:
                        client.request("GET", "/api/auth/me", expected={200})
                    self.assertEqual(caught.exception.kind, kind)
                    self.assertEqual(caught.exception.status, status)

            def http_503(args, **kwargs):
                Path(args[args.index("--output") + 1]).write_text('{"error":{"code":"busy"}}', encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="503", stderr="")

            with patch.object(runner.subprocess, "run", side_effect=http_503):
                with self.assertRaises(runner.SafeHttpError) as caught:
                    client.request("GET", "/api/auth/me", expected={200})
            self.assertEqual(caught.exception.kind, "http_response_error")
            self.assertEqual(caught.exception.status, 503)

            with patch.object(runner.subprocess, "run",
                              side_effect=subprocess.TimeoutExpired(cmd="curl", timeout=25)):
                with self.assertRaises(runner.SafeHttpError) as caught:
                    client.request("GET", "/api/auth/me", expected={200})
            self.assertEqual(caught.exception.kind, "transport_timeout")
            self.assertIsNone(caught.exception.status)
        finally:
            client.close()

    def test_clarification_is_incomplete_and_never_patches_an_unrelated_ticket(self):
        calls = []

        class FakeClient:
            ask_request_id = None
            ask_payload = None

            def __init__(self, _base):
                self.role = None

            def request(self, method, path, body=None, expected=None):
                calls.append((method, path))
                if path == "/api/auth/login":
                    self.role = "admin" if body["login_id"] == "qa-admin" else "employee"
                    return 200, {"user": {"id": 1 if self.role == "admin" else 2,
                                          "role": self.role, "must_change_password": False}}
                if path == "/api/auth/me":
                    return 200, {"id": 1 if self.role == "admin" else 2, "role": self.role}
                if path == "/api/admin/tickets":
                    return (200, {"items": []}) if self.role == "admin" else (403, {"error": {}})
                if path == "/api/ask":
                    FakeClient.ask_request_id = body["request_id"]
                    FakeClient.ask_payload = body
                    return 200, {"request_id": body["request_id"], "route": "보완 질문",
                                 "ticket": None, "sources": []}
                if path == "/api/my-requests":
                    return 200, {"items": [{"request_id": FakeClient.ask_request_id,
                                             "ticket": None}]}
                if path == "/api/auth/logout":
                    return 200, {"ok": True}
                raise AssertionError("unexpected API path")

        secrets = {
            "OKE_REAL_QA_EMPLOYEE_LOGIN": "qa-employee",
            "OKE_REAL_QA_EMPLOYEE_PASSWORD": "employee-secret",
            "OKE_REAL_QA_ADMIN_LOGIN": "qa-admin",
            "OKE_REAL_QA_ADMIN_PASSWORD": "admin-secret",
            "OKE_REAL_QA_WINDOW_RESERVED": "1",
            "OKE_REAL_QA_FE_READY": "1",
        }
        with patch.dict(runner.os.environ, secrets, clear=True), patch.object(runner, "Client", FakeClient):
            report = runner.run_live(runner.DEFAULT_BASE, runner.DEFAULT_QUESTION, 1, None)

        self.assertEqual(report["actual_route"], "보완 질문")
        self.assertEqual(report["verdict"], "INCOMPLETE_CLARIFICATION_NO_TICKET")
        self.assertFalse(report["admin_patch_attempted"])
        self.assertNotIn("PATCH", [method for method, _ in calls])
        self.assertNotEqual(report["verdict"], "PASS_API_SEQUENCE")
        self.assertEqual(FakeClient.ask_payload["question"], runner.DEFAULT_QUESTION)
        self.assertEqual(FakeClient.ask_payload["attempt"], 1)
        self.assertNotIn("context", FakeClient.ask_payload)
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("employee-secret", encoded)
        self.assertNotIn(runner.DEFAULT_QUESTION, encoded)

if __name__ == "__main__":
    unittest.main()
