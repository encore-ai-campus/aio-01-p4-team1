#!/usr/bin/env python3
"""Gated real-VM API support runner. Default mode is read-only preflight."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.parse
from uuid import uuid4


OWN = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "https://aio-t1.isitsoft.kr"
DEFAULT_QUESTION = (
    "재택근무 중 VPN 연결 시 인증 오류가 반복됩니다. 오늘 오전부터 발생했고 "
    "비밀번호를 다시 입력해도 동일합니다. 확인 방법을 알려주세요."
)


class SafeHttpError(Exception):
    def __init__(self, status: int | None, step: str, kind: str = "check_failure"):
        super().__init__(step)
        self.status = status
        self.step = step
        self.kind = kind


def curl_error_kind(returncode: int, stderr: str) -> str:
    lowered = stderr.lower()
    if returncode == 28 or "timed out" in lowered or "timeout" in lowered:
        return "transport_timeout"
    if returncode in {35, 51, 58, 59, 60, 77, 80, 82, 83, 90} or "ssl" in lowered or "certificate" in lowered:
        return "tls_transport_error"
    return "network_transport_error"


class Client:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self._private = tempfile.TemporaryDirectory(prefix="oke-real-qa-")
        os.chmod(self._private.name, 0o700)
        self._cookie_file = Path(self._private.name) / "cookies.txt"
        self._response_file = Path(self._private.name) / "response.body"
        fd = os.open(self._cookie_file, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)
        os.chmod(self._cookie_file, 0o600)
        fd = os.open(self._response_file, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)
        os.chmod(self._response_file, 0o600)

    def close(self) -> None:
        self._private.cleanup()

    def request(self, method: str, path: str, body: dict | None = None,
                expected: set[int] | None = None) -> tuple[int, object]:
        data = "" if body is None else json.dumps(body, ensure_ascii=False)
        args = ["curl", "--silent", "--show-error", "--proto", "=https",
                "--tlsv1.2", "--max-time", "20",
                "--request", method, "--header", "Accept: application/json",
                "--header", "Content-Type: application/json",
                "--cookie", str(self._cookie_file), "--cookie-jar", str(self._cookie_file),
                "--output", str(self._response_file), "--write-out", "%{http_code}",
                self.base + path]
        if body is not None:
            args[1:1] = ["--data-binary", "@-"]
        try:
            child_env = os.environ.copy()
            for key in ("OKE_REAL_QA_EMPLOYEE_LOGIN", "OKE_REAL_QA_EMPLOYEE_PASSWORD",
                        "OKE_REAL_QA_ADMIN_LOGIN", "OKE_REAL_QA_ADMIN_PASSWORD"):
                child_env.pop(key, None)
            completed = subprocess.run(args, input=data if body is not None else None,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25,
                check=False, env=child_env)
        except subprocess.TimeoutExpired:
            raise SafeHttpError(None, "transport_timeout", "transport_timeout") from None
        except OSError:
            raise SafeHttpError(None, "curl_unavailable", "network_transport_error") from None
        if completed.returncode != 0:
            # curl stderr can contain transport details; retain only a safe category.
            kind = curl_error_kind(completed.returncode, completed.stderr)
            raise SafeHttpError(None, kind, kind)
        if not completed.stdout.isdigit():
            raise SafeHttpError(None, "invalid_http_status")
        status = int(completed.stdout)
        try:
            raw = self._response_file.read_bytes()
        except OSError:
            raise SafeHttpError(status, "response_read_error") from None
        if len(raw) > 2_000_000:
            raise SafeHttpError(status, "response_too_large")
        try:
            parsed: object = json.loads(raw) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = raw.decode("utf-8", errors="replace")
        if expected is not None and status not in expected:
            raise SafeHttpError(status, "unexpected_http_status", "http_response_error")
        return status, parsed


def safe_user(client: Client, login_id: str, password: str, role: str) -> dict:
    status, body = client.request("POST", "/api/auth/login",
                                  {"login_id": login_id, "password": password}, {200})
    if not isinstance(body, dict) or not isinstance(body.get("user"), dict):
        raise SafeHttpError(status, "invalid_login_response")
    user = body["user"]
    if user.get("role") != role or user.get("must_change_password") is not False:
        raise SafeHttpError(status, "role_or_password_setup_not_ready")
    status, me = client.request("GET", "/api/auth/me", expected={200})
    if not isinstance(me, dict) or me.get("id") != user.get("id") or me.get("role") != role:
        raise SafeHttpError(status, "session_identity_mismatch")
    return user


def items_from(body: object, status: int, step: str) -> list[dict]:
    if not isinstance(body, dict) or not isinstance(body.get("items"), list):
        raise SafeHttpError(status, step)
    return [item for item in body["items"] if isinstance(item, dict)]


def ticket_for_request(items: list[dict], request_id: str, status: int) -> dict:
    matches = [item for item in items if item.get("request_id") == request_id]
    if len(matches) != 1:
        raise SafeHttpError(status, "request_ticket_not_unique")
    return matches[0]


def validate_base(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme != "https" or parsed.hostname != "aio-t1.isitsoft.kr"
            or parsed.port not in (None, 443)
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ("", "/")):
        raise ValueError("base URL must be the approved public HTTPS origin")
    return DEFAULT_BASE


def run_preflight(base: str) -> dict:
    client = Client(base)
    started = time.monotonic()
    try:
        status, page = client.request("GET", "/login", expected={200})
        login_html = isinstance(page, str) and "로그인" in page
        auth_status, auth_body = client.request("GET", "/api/auth/me", expected={401})
        return {
            "mode": "read_only_preflight", "base_origin": base,
            "checks": {
                "login_http_200": status == 200,
                "login_page_has_login_label": login_html,
                "anonymous_me_http_401": auth_status == 401,
            },
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "write_requests": 0,
            "auth_response_body_recorded": False,
        }
    finally:
        client.close()


def run_live(base: str, question: str, attempt: int, context: str | None) -> dict:
    if not question.strip() or len(question) > 500:
        raise ValueError("question must be 1..500 characters")
    if not 1 <= attempt <= 3:
        raise ValueError("attempt must be 1..3")
    if context is not None and len(context) > 2000:
        raise ValueError("context must be at most 2000 characters")
    required = {
        "OKE_REAL_QA_EMPLOYEE_LOGIN": "employee login ID",
        "OKE_REAL_QA_EMPLOYEE_PASSWORD": "employee password",
        "OKE_REAL_QA_ADMIN_LOGIN": "admin login ID",
        "OKE_REAL_QA_ADMIN_PASSWORD": "admin password",
    }
    missing = [label for key, label in required.items() if not os.environ.get(key)]
    if missing:
        raise ValueError("missing secret inputs: " + ", ".join(missing))
    if os.environ.get("OKE_REAL_QA_WINDOW_RESERVED") != "1":
        raise ValueError("reserved VM mutation window handoff is required")
    if os.environ.get("OKE_REAL_QA_FE_READY") != "1":
        raise ValueError("frontend and account handoff readiness is required")

    login_id = os.environ["OKE_REAL_QA_EMPLOYEE_LOGIN"]
    password = os.environ["OKE_REAL_QA_EMPLOYEE_PASSWORD"]
    admin_id = os.environ["OKE_REAL_QA_ADMIN_LOGIN"]
    admin_password = os.environ["OKE_REAL_QA_ADMIN_PASSWORD"]
    employee = Client(base)
    admin = Client(base)
    report: dict = {
        "mode": "live_api_sequence", "base_origin": base,
        "request_id": "real-qa-" + uuid4().hex,
        "input_profile": "explicit" if question != DEFAULT_QUESTION else "default_vpn_attempt_1",
        "attempt": attempt,
        "source_evidence": [], "ask_elapsed_seconds": None,
        "write_requests": 0, "ticket_id": None,
        "ticket_count_before_api_view": None, "ticket_count_after_api_view": None,
        "checks": {}, "failed_step": None, "failure_type": None,
        "mutation_outcome_uncertain": False,
        "db_count_snapshot": "not_collected_by_this_client",
    }
    rid = report["request_id"]
    try:
        safe_user(admin, admin_id, admin_password, "admin")
        code, before_body = admin.request("GET", "/api/admin/tickets", expected={200})
        before = items_from(before_body, code, "admin_ticket_list_before")
        report["ticket_count_before_api_view"] = len(before)

        safe_user(employee, login_id, password, "employee")
        code, denied = employee.request("GET", "/api/admin/tickets", expected={403})
        report["checks"]["employee_admin_forbidden_403"] = code == 403
        report["checks"]["forbidden_body_not_recorded"] = denied is not None

        report["write_requests"] += 1
        try:
            payload = {"request_id": rid, "question": question, "attempt": attempt}
            if context:
                payload["context"] = context
            ask_started = time.monotonic()
            try:
                code, ask = employee.request("POST", "/api/ask", payload, {200})
            finally:
                report["ask_elapsed_seconds"] = round(time.monotonic() - ask_started, 3)
        except SafeHttpError:
            report["mutation_outcome_uncertain"] = True
            raise
        if not isinstance(ask, dict) or ask.get("request_id") != rid:
            report["mutation_outcome_uncertain"] = True
            raise SafeHttpError(code, "ask_response_missing_request_id")
        route = ask.get("route")
        report["actual_route"] = route if isinstance(route, str) else None
        sources = ask.get("sources")
        if not isinstance(sources, list):
            raise SafeHttpError(code, "sources_not_list")
        report["source_evidence"] = [
            {"doc": item.get("doc"), "score": item.get("score")}
            for item in sources
            if isinstance(item, dict) and isinstance(item.get("doc"), str)
            and (item.get("score") is None or type(item.get("score")) in (int, float))
        ]
        if len(report["source_evidence"]) != len(sources):
            raise SafeHttpError(code, "source_evidence_shape_invalid")
        ticket = ask.get("ticket")
        if route == "담당자 이관":
            if (not isinstance(ticket, dict) or not isinstance(ticket.get("ticket_id"), str)
                    or not ticket["ticket_id"]):
                raise SafeHttpError(code, "handoff_route_missing_ticket")
            report["ticket_id"] = ticket["ticket_id"]
            report["checks"]["ask_created_one_ticket_response"] = True
        elif route == "보완 질문":
            if ticket is not None:
                raise SafeHttpError(code, "clarification_unexpectedly_has_ticket")
        elif route == "자동 답변":
            if ticket is not None or not ask.get("sources"):
                raise SafeHttpError(code, "answer_missing_sources_or_ticket_not_null")
        else:
            raise SafeHttpError(code, "unsupported_or_blocked_ask_route")

        code, own_before = employee.request("GET", "/api/my-requests", expected={200})
        own_items = items_from(own_before, code, "employee_request_list_before_logout")
        saved = [item for item in own_items if item.get("request_id") == rid]
        if len(saved) != 1:
            raise SafeHttpError(code, "inquiry_not_persisted_in_employee_list")
        report["checks"]["inquiry_saved_and_listed_before_logout"] = True

        code, _ = employee.request("POST", "/api/auth/logout", expected={200})
        report["checks"]["employee_logout_http_200"] = code == 200
        employee = Client(base)
        safe_user(employee, login_id, password, "employee")
        code, own_after_login = employee.request("GET", "/api/my-requests", expected={200})
        own_items = items_from(own_after_login, code, "employee_request_list_after_relogin")
        saved = [item for item in own_items if item.get("request_id") == rid]
        if len(saved) != 1:
            raise SafeHttpError(code, "inquiry_missing_after_relogin")
        saved_ticket = saved[0].get("ticket")
        if report["ticket_id"] is not None:
            if not isinstance(saved_ticket, dict) or saved_ticket.get("ticket_id") != report["ticket_id"]:
                raise SafeHttpError(code, "ticket_link_missing_after_relogin")
            report["checks"]["inquiry_and_ticket_visible_after_relogin"] = True
        elif saved_ticket is not None:
            raise SafeHttpError(code, "ticketless_route_has_ticket_in_saved_inquiry")
        else:
            report["checks"]["inquiry_visible_after_relogin_without_ticket"] = True
            report["verdict"] = ("INCOMPLETE_CLARIFICATION_NO_TICKET" if route == "보완 질문"
                                  else "INCOMPLETE_NO_TICKET_FOR_ADMIN_PATCH")
            report["admin_patch_attempted"] = False
            return report

        code, admin_after = admin.request("GET", "/api/admin/tickets", expected={200})
        admin_items = items_from(admin_after, code, "admin_ticket_list_after_create")
        row = ticket_for_request(admin_items, rid, code)
        if row.get("ticket_id") != report["ticket_id"]:
            raise SafeHttpError(code, "ticket_id_mismatch_in_admin_list")
        entity_id = row.get("id")
        if type(entity_id) is not int or entity_id < 1:
            raise SafeHttpError(code, "invalid_admin_ticket_entity_id")
        report["checks"]["admin_ticket_query_found_created_row"] = True

        report["write_requests"] += 1
        try:
            code, patched = admin.request("PATCH", "/api/admin/tickets/" + str(entity_id), {
                "status": "in_progress", "reply": "실제 연동 QA 처리 확인",
            }, {200})
        except SafeHttpError:
            report["mutation_outcome_uncertain"] = True
            raise
        if (not isinstance(patched, dict) or patched.get("request_id") != rid
                or patched.get("status") != "in_progress"
                or patched.get("reply") != "실제 연동 QA 처리 확인"):
            report["mutation_outcome_uncertain"] = True
            raise SafeHttpError(code, "admin_ticket_update_not_confirmed")
        code, verify_body = admin.request("GET", "/api/admin/tickets", expected={200})
        verify_row = ticket_for_request(items_from(verify_body, code, "admin_ticket_list_after_patch"), rid, code)
        if verify_row.get("status") != "in_progress" or verify_row.get("reply") != "실제 연동 QA 처리 확인":
            raise SafeHttpError(code, "admin_ticket_update_not_persistent")
        report["ticket_count_after_api_view"] = len(items_from(verify_body, code, "admin_ticket_list_after_patch"))
        report["checks"]["admin_status_and_reply_persisted"] = True

        code, final_requests = employee.request("GET", "/api/my-requests", expected={200})
        final_items = items_from(final_requests, code, "employee_request_list_after_admin_update")
        final_match = [item for item in final_items if item.get("request_id") == rid]
        if len(final_match) != 1:
            raise SafeHttpError(code, "inquiry_missing_after_admin_update")
        final_ticket = final_match[0].get("ticket")
        report["checks"]["employee_latest_ticket_status_visible"] = (
            isinstance(final_ticket, dict) and final_ticket.get("status") == "in_progress")
        report["checks"]["employee_latest_reply_visible"] = (
            isinstance(final_ticket, dict) and final_ticket.get("reply") == "실제 연동 QA 처리 확인")
        report["verdict"] = "PASS_API_SEQUENCE" if all(report["checks"].values()) else "INCOMPLETE_API_SEQUENCE"
    except SafeHttpError as error:
        report["failed_step"] = error.step
        report["http_status"] = error.status
        report["failure_type"] = error.kind
        report["verdict"] = "FAIL_OR_INCOMPLETE"
    except Exception as error:  # report class only; exception text may contain request data
        report["failed_step"] = "unexpected"
        report["failure_type"] = type(error).__name__
        report["verdict"] = "FAIL_OR_INCOMPLETE"
    finally:
        for client in (employee, admin):
            close = getattr(client, "close", None)
            if close is not None:
                close()
    return report


def write_report(path: Path, report: dict) -> None:
    path = path.resolve()
    if not path.is_relative_to(OWN / "runs") or path.suffix != ".json" or path.exists():
        raise ValueError("report must be a new JSON file directly under develop/wonmin/runs")
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=os.environ.get("OKE_REAL_QA_BASE", DEFAULT_BASE))
    parser.add_argument("--question", default=DEFAULT_QUESTION,
                        help="actual first inquiry; 1..500 chars; omitted from reports")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--context", help="optional context; omitted from reports")
    parser.add_argument("--execute-live-writes", action="store_true",
                        help="run only after reserved-window and FE/account handoff environment gates")
    parser.add_argument("--output", help="new JSON report path under develop/wonmin/runs")
    args = parser.parse_args()
    try:
        base = validate_base(args.base)
        report = (run_live(base, args.question, args.attempt, args.context)
                  if args.execute_live_writes else run_preflight(base))
        if args.output:
            write_report(OWN / args.output, report)
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
        return 0 if report.get("verdict") in (None, "PASS_API_SEQUENCE") and all(report.get("checks", {}).values()) else 1
    except SafeHttpError as error:
        print(json.dumps({"verdict": "NOT_RUN", "failure_type": error.kind,
                          "http_status": error.status}, ensure_ascii=False))
        return 2
    except Exception as error:
        print(json.dumps({"verdict": "NOT_RUN", "failure_type": type(error).__name__}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
