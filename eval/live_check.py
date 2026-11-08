#!/usr/bin/env python3
"""Focused live API/DB checks. This is not the official common-14 runner.

Credentials are read from environment or a private env file, never from arguments.
Reports contain only allowlisted measurements, not bodies, passwords or cookies.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import http.cookiejar
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4

NORMAL_QUESTION = "비밀번호를 바꾸려면 어떤 규칙을 지켜야 하나요?"
HANDOFF_QUESTION = "접속이 안 돼요"
ENV_KEYS = {"OKE_EMP_USER", "OKE_EMP_PASS", "OKE_ADMIN_USER", "OKE_ADMIN_PASS",
            "VM_WEB_URL", "VM_USER", "VM_PASSWORD", "OKE_TEAM_KEY"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def load_settings(path=None):
    values = {}
    if path:
        for line in Path(path).read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, sep, value = line.partition("=")
            key = key.strip()
            if sep and key in ENV_KEYS:
                values[key] = value.strip().strip("\"'")
    values.update({k: os.environ[k] for k in ENV_KEYS if k in os.environ})
    return values


def validate_origin(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("base URL must be an origin without credentials")
    if not parsed.hostname or (parsed.scheme != "https" and not
            (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"})):
        raise ValueError("HTTPS is required outside localhost")
    return url.rstrip("/")


class Session:
    def __init__(self, origin):
        self.origin = validate_origin(origin)
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            NoRedirect(), urllib.request.HTTPCookieProcessor(self.cookies))
        self.logged_in = False

    def call(self, path, body=None, *, headers=None):
        request = urllib.request.Request(self.origin + path,
            data=None if body is None else json.dumps(body, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json", **(headers or {})},
            method="GET" if body is None else "POST")
        start = time.monotonic()
        try:
            response = self.opener.open(request, timeout=35)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError("response size exceeded")
            try:
                data = json.loads(raw)
            except (ValueError, UnicodeError):
                data = {}
            return response.code, data, round(time.monotonic() - start, 3)

    def login(self, username, password):
        status, data, _ = self.call("/api/auth/login", {"login_id": username, "password": password})
        self.logged_in = status == 200
        return self.logged_in and data.get("user", {}).get("must_change_password") is False

    def logout(self):
        if self.logged_in:
            status, _, _ = self.call("/api/auth/logout", {})
            self.logged_in = False
            return status == 200
        return True


def measure_response(status, body, elapsed):
    """Explicit allowlist: no answer, question, contact, identity or auth values."""
    sources = body.get("sources", [])
    ticket = body.get("ticket")
    return {"http_status": status, "elapsed_sec": elapsed,
        "route": body.get("route"), "source_count": len(sources) if isinstance(sources, list) else 0,
        "source_docs": sorted({s["doc"] for s in sources if isinstance(s, dict)
                                and isinstance(s.get("doc"), str)}) if isinstance(sources, list) else [],
        "ticket_id": ticket.get("ticket_id") if isinstance(ticket, dict) else None,
        "duplicate": ticket.get("duplicate") if isinstance(ticket, dict) else None}


def assess_normal(record):
    return {"http_200": record["http_status"] == 200,
        "automatic_answer": record["route"] == "자동 답변",
        "password_policy_source": "password-policy" in record["source_docs"],
        "no_ticket": record["ticket_id"] is None,
        "within_8_seconds": record["elapsed_sec"] <= 8.0}


def assess_db(receipt, ticket_id):
    return {"one_inquiry": receipt.get("inquiries") == 1,
        "one_ticket": receipt.get("tickets") == 1,
        "one_alert": receipt.get("alerts") == 1,
        "inquiry_completed": receipt.get("completed") == 1,
        "owner_and_keys_match": receipt.get("linked") == 1,
        "response_ticket_matches": receipt.get("response_match") == 1,
        "api_db_ticket_matches": receipt.get("ticket_ids") == [ticket_id],
        "no_dlq_for_request": receipt.get("dlq") == 0}


async def vm_receipt(settings, request_id):
    from vm_access import VMTerminal
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", request_id):
        raise ValueError("unsafe request ID")
    sql = """SELECT count(DISTINCT i.id) inquiries, count(DISTINCT t.id) tickets,
        count(DISTINCT a.id) alerts,
        count(DISTINCT i.id) FILTER (WHERE i.status='completed') completed,
        count(DISTINCT t.id) FILTER (WHERE t.inquiry_id=i.id AND t.request_key=i.request_id
            AND t.requester_id=i.requester_id) linked,
        count(DISTINCT t.id) FILTER (WHERE i.result->'ticket'->>'ticket_id'=t.ticket_id) response_match,
        coalesce(jsonb_agg(DISTINCT t.ticket_id) FILTER (WHERE t.ticket_id IS NOT NULL),'[]') ticket_ids,
        (SELECT count(*) FROM app.dlq WHERE request_id=:rid) dlq
        FROM app.inquiries i LEFT JOIN app.tickets t ON t.request_key=i.request_id
        LEFT JOIN app.alerts a ON a.ticket_id=t.id WHERE i.request_id=:rid"""
    # DB connection settings stay inside the existing backend container.
    code = ("import json,os; from sqlalchemy import create_engine,text; "
        "engine=create_engine(os.environ['DATABASE_URL']); "
        "connection=engine.connect(); transaction=connection.begin(); "
        "connection.exec_driver_sql('SET TRANSACTION READ ONLY'); "
        "connection.exec_driver_sql(\"SET LOCAL statement_timeout='5s'\"); "
        f"row=connection.execute(text({sql!r}),{{'rid':{request_id!r}}}).mappings().one(); "
        "print(json.dumps(dict(row))); transaction.rollback(); connection.close(); engine.dispose()")
    command = "docker exec oke-backend-1 python -c " + shlex.quote(code)
    async with VMTerminal(settings.get("VM_WEB_URL", "https://aio-t1.isitsoft.kr/ssh/"),
                          settings.get("VM_USER", "toor"), settings["VM_PASSWORD"]) as terminal:
        version_code, version = await terminal.run("git -C /home/toor/Aio-4pj-1team rev-parse HEAD")
        exit_code, output = await terminal.run(command)
    if exit_code or version_code:
        raise RuntimeError("VM receipt command failed")
    result = json.loads(output)
    result["vm_checkout_commit"] = version.strip()
    return result


def local_commit():
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def run_checks(origin, settings, *, normal_repeats=3, with_vm_db=False):
    report = {"schema": "oke-live-smoke-v1", "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": origin, "runner_source_commit": local_commit(),
        "scope": "real API + optional read-only VM DB; not official common-14",
        "latency_condition": "first observed request and subsequent independent requests; service not restarted",
        "normal": [], "handoff": [], "checks": {}, "errors": [], "verdict": "FAIL"}
    employee, admin = Session(origin), Session(origin)
    checks = report["checks"]
    try:
        checks["employee_login"] = employee.login(settings["OKE_EMP_USER"], settings["OKE_EMP_PASS"])
        if not checks["employee_login"]:
            return report
        for _ in range(normal_repeats):
            request_id = "audit-normal-" + uuid4().hex
            status, body, elapsed = employee.call("/api/ask", {
                "request_id": request_id, "question": NORMAL_QUESTION, "attempt": 1})
            row = {"request_id": request_id, **measure_response(status, body, elapsed)}
            row["checks"] = assess_normal(row)
            report["normal"].append(row)
        checks["normal_all"] = all(all(r["checks"].values()) for r in report["normal"])
        request_id = "audit-handoff-" + uuid4().hex
        report["handoff_request_id"] = request_id
        payload = {"request_id": request_id, "question": HANDOFF_QUESTION,
                   "attempt": 3, "context": "회사 서비스에 접속하려는 중입니다."}
        for index in range(2):
            status, body, elapsed = employee.call("/api/ask", payload)
            row = measure_response(status, body, elapsed)
            report["handoff"].append(row)
            checks[f"handoff_{index+1}"] = status == 200 and row["route"] == "담당자 이관" and bool(row["ticket_id"])
            if with_vm_db and checks[f"handoff_{index+1}"]:
                receipt = asyncio.run(vm_receipt(settings, request_id))
                report[f"db_after_{index+1}"] = receipt
                checks[f"db_after_{index+1}"] = all(assess_db(receipt, row["ticket_id"]).values())
        first, second = report["handoff"]
        checks["same_ticket"] = bool(first["ticket_id"]) and first["ticket_id"] == second["ticket_id"]
        checks["duplicate_false_then_true"] = first["duplicate"] is False and second["duplicate"] is True
        status, body, _ = employee.call("/api/my-requests")
        own = [row for row in body.get("items", []) if row.get("request_id") == request_id]
        checks["own_list_once"] = status == 200 and len(own) == 1 and (own[0].get("ticket") or {}).get("ticket_id") == first["ticket_id"]
        status, _, _ = employee.call("/api/admin/tickets")
        checks["employee_admin_denied"] = status == 403
        checks["admin_login"] = admin.login(settings["OKE_ADMIN_USER"], settings["OKE_ADMIN_PASS"])
        if checks["admin_login"]:
            status, body, _ = admin.call("/api/admin/tickets")
            tickets = [r for r in body.get("items", []) if r.get("request_id") == request_id]
            checks["admin_ticket_once"] = status == 200 and len(tickets) == 1 and tickets[0].get("ticket_id") == first["ticket_id"]
            status, body, _ = admin.call("/api/admin/alerts")
            alerts = [r for r in body.get("items", []) if r.get("ticket_id") == first["ticket_id"]]
            checks["admin_alert_once"] = status == 200 and len(alerts) == 1
        report["verdict"] = ("PASS" if with_vm_db else "PARTIAL_NO_DB_RECEIPT") if all(checks.values()) else "FAIL"
    except Exception as error:
        # Exceptions may contain private URLs/connection strings. Record the class only.
        report["errors"].append(type(error).__name__)
    finally:
        for name, session in [("employee", employee), ("admin", admin)]:
            try:
                checks[f"{name}_logout"] = session.logout()
            except Exception as error:
                checks[f"{name}_logout"] = False
                report["errors"].append(type(error).__name__)
        if not all(checks.values()):
            report["verdict"] = "FAIL"
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://aio-t1.isitsoft.kr")
    parser.add_argument("--env-file", help="private env file; values never printed")
    parser.add_argument("--vm-db", action="store_true", help="read-only VM DB receipts (requires websockets)")
    parser.add_argument("--receipt-only", action="store_true", help="verify an existing request without API writes or login")
    parser.add_argument("--request-id", help="existing request ID for --receipt-only")
    parser.add_argument("--expected-ticket-id", help="known ticket ID for --receipt-only")
    parser.add_argument("--normal-repeats", type=int, default=3, choices=range(1, 6))
    parser.add_argument("--output", required=True, help="new sanitized JSON report; existing files are never overwritten")
    args = parser.parse_args()
    origin = validate_origin(args.base_url)
    output = Path(args.output)
    if output.exists():
        parser.error("output already exists")
    settings = load_settings(args.env_file)
    required = set() if args.receipt_only else {"OKE_EMP_USER", "OKE_EMP_PASS", "OKE_ADMIN_USER", "OKE_ADMIN_PASS"}
    if args.vm_db or args.receipt_only:
        required.add("VM_PASSWORD")
    missing = sorted(k for k in required if not settings.get(k))
    if missing:
        parser.error("missing private settings: " + ", ".join(missing))
    if args.receipt_only:
        if not args.request_id or not args.expected_ticket_id:
            parser.error("--receipt-only requires --request-id and --expected-ticket-id")
        report = {"schema": "oke-db-link-receipt-v1", "target": origin,
            "scope": "read-only DB check of existing request; no API replay or login test",
            "request_id": args.request_id, "runner_source_commit": local_commit(),
            "started_at_utc": datetime.now(timezone.utc).isoformat(), "errors": [], "checks": {}, "verdict": "FAIL"}
        try:
            report["db_receipt"] = asyncio.run(vm_receipt(settings, args.request_id))
            report["checks"] = assess_db(report["db_receipt"], args.expected_ticket_id)
            report["verdict"] = "PASS_DB_LINK_ONLY" if all(report["checks"].values()) else "FAIL"
        except Exception as error:
            report["errors"].append(type(error).__name__)
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    else:
        report = run_checks(origin, settings, normal_repeats=args.normal_repeats, with_vm_db=args.vm_db)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"verdict": report["verdict"], "output": str(output),
                      "failed_checks": [k for k,v in report["checks"].items() if not v],
                      "errors": report["errors"]},ensure_ascii=False))
    return 0 if report["verdict"] in {"PASS", "PASS_DB_LINK_ONLY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
