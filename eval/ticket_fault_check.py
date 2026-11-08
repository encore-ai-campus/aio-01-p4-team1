#!/usr/bin/env python3
"""One request's live ticket failure, independent alerts/DLQ, and same-ID recovery.

Requires the deployed ticket fault gate and its read-only operator directory mount.
Credentials use the same private settings as live_check.py. No public fault API exists.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import shlex
from uuid import uuid4

from live_check import Session, load_settings, local_commit, measure_response
from vm_access import VMTerminal

FAULT_FILE = "/home/toor/.config/oke/ticket-fault/active.json"


async def remote(settings, code):
    async with VMTerminal(settings.get("VM_WEB_URL", "https://aio-t1.isitsoft.kr/ssh/"),
                          settings.get("VM_USER", "toor"), settings["VM_PASSWORD"]) as terminal:
        status, output = await terminal.run("python3 -c " + shlex.quote(code), timeout=35)
    if status:
        raise RuntimeError("VM command failed")
    return json.loads(output)


async def switch(settings, request_id, *, enable):
    # IDs are generated here, not accepted from untrusted HTTP input.
    code = f"""
import json,os,time
from pathlib import Path
p=Path({FAULT_FILE!r}); rid={request_id!r}
if {enable!r}:
 p.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
 now=time.time()
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
 with os.fdopen(fd,'w') as f:json.dump({{'request_id':rid,'armed_at':now,'expires_at':now+300}},f)
 print(json.dumps({{'armed':True,'expires_in_seconds':300}}))
else:
 if p.exists():
  rule=json.loads(p.read_text())
  if rule.get('request_id')!=rid:raise RuntimeError('different operator rule')
  p.unlink()
 print(json.dumps({{'disarmed':not p.exists()}}))
"""
    return await remote(settings, code)


async def deployment_state(settings):
    code = """import json,subprocess
x=json.loads(subprocess.check_output(['docker','inspect','oke-backend-1']))[0]
env=dict(v.split('=',1) for v in x['Config']['Env'])
print(json.dumps({'service_mode':env.get('SERVICE_MODE'),'image_id':x['Image'],
 'readonly_fault_mount':any(m['Destination']=='/run/oke-ticket-fault' and not m['RW'] for m in x['Mounts'])}))
"""
    return await remote(settings, code)


async def receipt(settings, request_id):
    sql = """SELECT
      (SELECT count(*) FROM app.inquiries WHERE request_id=:rid) inquiries,
      (SELECT count(*) FROM app.inquiries WHERE request_id=:rid AND status='completed') completed,
      (SELECT count(*) FROM app.tickets WHERE request_key=:rid) tickets,
      (SELECT count(*) FROM app.alerts WHERE event_key=:failure_key) failure_alerts,
      (SELECT count(*) FROM app.alerts WHERE event_key=:ticket_key) ticket_alerts,
      (SELECT count(*) FROM app.dlq WHERE request_id=:rid AND reason='tickets_down') dlq,
      (SELECT count(*) FROM app.dlq WHERE request_id=:rid AND status='pending') pending_dlq,
      (SELECT count(*) FROM app.tickets t JOIN app.inquiries i ON t.inquiry_id=i.id
       WHERE i.request_id=:rid AND t.request_key=i.request_id AND t.requester_id=i.requester_id
       AND i.result->'ticket'->>'ticket_id'=t.ticket_id) linked"""
    inner = ("import json,os; from sqlalchemy import create_engine,text; "
        "e=create_engine(os.environ['DATABASE_URL']); c=e.connect(); tx=c.begin(); "
        "c.exec_driver_sql('SET TRANSACTION READ ONLY'); "
        "c.exec_driver_sql(\"SET LOCAL statement_timeout='5s'\"); "
        f"r=c.execute(text({sql!r}),{{'rid':{request_id!r},'failure_key':{(request_id+':tickets-down')!r},'ticket_key':{(request_id+':ticket-created')!r}}}).mappings().one(); "
        "print(json.dumps(dict(r))); tx.rollback(); c.close(); e.dispose()")
    command = "docker exec oke-backend-1 python -c " + shlex.quote(inner)
    code = ("import json,subprocess; "
            f"p=subprocess.run({shlex.split(command)!r},capture_output=True,text=True); "
            "assert p.returncode==0; print(p.stdout)")
    return await remote(settings, code)


def run(settings, output):
    report = {"schema": "oke-app-ticket-fault-v1", "target": "https://aio-t1.isitsoft.kr",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "runner_source_commit": local_commit(),
        "runner_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": {}, "errors": [],
        "scope": "real authenticated FastAPI -> n8n -> app PostgreSQL; one scoped ticket-write fault",
        "limits": ["This injects a ticket API 503 before its database write; the database remains available.",
                   "No browser clicks or whole-database outage tested.",
                   "Recovery is an explicit same-ID retry; existing DLQ records are not automatically drained."]}
    checks = report["checks"]
    employee = Session(report["target"])
    request_id = "audit-fault-" + uuid4().hex
    report["request_id"] = request_id
    payload = {"request_id": request_id,
               "question": "사내 식당 앱이 열리지 않아요. 담당자 점검을 요청합니다",
               "attempt": 1}
    armed = False
    try:
        report["deployment"] = state = asyncio.run(deployment_state(settings))
        checks["app_mode_and_readonly_gate"] = (state["service_mode"] == "app"
            and state["readonly_fault_mount"] is True)
        if not checks["app_mode_and_readonly_gate"]:
            return report
        checks["employee_login"] = employee.login(settings["OKE_EMP_USER"], settings["OKE_EMP_PASS"])
        if not checks["employee_login"]:
            return report
        armed = True
        report["switch"] = asyncio.run(switch(settings, request_id, enable=True))
        status, body, elapsed = employee.call("/api/ask", payload)
        report["fault_response"] = measure_response(status, body, elapsed)
        report["fault_response"]["reason"] = body.get("reason")
        checks["fault_safe_response"] = (status == 200 and body.get("route") == "담당자 이관"
            and body.get("ticket") is None and body.get("reason") == "tickets_down")
        checks["no_false_success_message"] = ("접수 여부를 확인하지 못했습니다" in body.get("answer", "")
            and "같은 요청 ID" in body.get("answer", ""))
        report["fault_db"] = fault = asyncio.run(receipt(settings, request_id))
        checks["fault_inquiry_saved_once"] = fault["inquiries"] == fault["completed"] == 1
        checks["fault_no_ticket"] = fault["tickets"] == 0
        checks["fault_alert_saved_once"] = fault["failure_alerts"] == 1 and fault["ticket_alerts"] == 0
        checks["fault_dlq_saved_once"] = fault["dlq"] == fault["pending_dlq"] == 1
        # An unrelated real inquiry must continue working while this request remains faulted.
        status, body, elapsed = employee.call("/api/ask", {
            "request_id": "fault-control-" + uuid4().hex,
            "question": "비밀번호를 바꾸려면 어떤 규칙을 지켜야 하나요?", "attempt": 1})
        report["unrelated_request"] = measure_response(status, body, elapsed)
        checks["other_request_unaffected"] = (status == 200 and body.get("route") == "자동 답변"
            and any(s.get("doc") == "password-policy" for s in body.get("sources", [])))
        report["disarm"] = asyncio.run(switch(settings, request_id, enable=False))
        armed = False
        checks["fault_disarmed"] = report["disarm"]["disarmed"]
        status, body, elapsed = employee.call("/api/ask", payload)
        report["recovery_response"] = measure_response(status, body, elapsed)
        ticket_id = report["recovery_response"]["ticket_id"]
        checks["same_id_recovery"] = (status == 200 and body.get("request_id") == request_id
            and body.get("route") == "담당자 이관" and bool(ticket_id))
        report["recovery_db"] = recovered = asyncio.run(receipt(settings, request_id))
        checks["recovery_one_linked_ticket"] = recovered["inquiries"] == recovered["completed"] == recovered["tickets"] == recovered["linked"] == 1
        checks["recovery_one_ticket_alert"] = recovered["ticket_alerts"] == recovered["failure_alerts"] == 1
        checks["original_dlq_retained"] = recovered["dlq"] == recovered["pending_dlq"] == 1
        status, body, _ = employee.call("/api/my-requests")
        own = [r for r in body.get("items", []) if r.get("request_id") == request_id]
        checks["employee_sees_recovered_ticket"] = (bool(ticket_id) and status == 200 and len(own) == 1
            and (own[0].get("ticket") or {}).get("ticket_id") == ticket_id)
    except Exception as error:
        report["errors"].append(type(error).__name__)
    finally:
        if armed:
            try:
                report["disarm"] = asyncio.run(switch(settings, request_id, enable=False))
                checks["fault_disarmed"] = report["disarm"]["disarmed"]
            except Exception as error:
                checks["fault_disarmed"] = False
                report["errors"].append(type(error).__name__)
        try:
            checks["employee_logout"] = employee.logout()
        except Exception as error:
            checks["employee_logout"] = False
            report["errors"].append(type(error).__name__)
        report["verdict"] = "PASS_APP_TICKET_FAULT" if checks and all(checks.values()) and not report["errors"] else "FAIL_OR_PARTIAL"
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        with output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", help="private settings; no credentials in command arguments")
    parser.add_argument("--output", required=True, type=Path, help="new sanitized report")
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("output must be a new file inside an existing directory")
    settings = load_settings(args.env_file)
    missing = [key for key in ["VM_PASSWORD", "OKE_EMP_USER", "OKE_EMP_PASS"] if not settings.get(key)]
    if missing:
        parser.error("missing private settings: " + ", ".join(missing))
    report = run(settings, args.output)
    print(json.dumps({"verdict": report["verdict"], "output": str(args.output),
        "failed_checks": [k for k, v in report["checks"].items() if not v],
        "errors": report["errors"]}, ensure_ascii=False))
    return 0 if report["verdict"] == "PASS_APP_TICKET_FAULT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
