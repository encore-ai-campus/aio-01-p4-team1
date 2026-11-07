#!/usr/bin/env python3
"""공용 VM oke-handoff WF-09(동일 request_id 멱등성) 재시험.

VM은 조회만 한다(설치·수정·재시작 없음). 실제 handoff 호출은 --run일 때만 하며 티켓 1건을 만든다.

준비: 저장소 루트 .env에 N8N_BASE, TEAM_KEY, VM_WEB_URL, VM_USER, VM_PASSWORD
      로컬 python에 websockets (VM에는 설치하지 않는다)

사용 (저장소 루트에서):
  python3 develop/wonmin/tools/live-wf09-check.py            # 사전 점검만: VM 게시본 구조 확인, 쓰기 없음
  python3 develop/wonmin/tools/live-wf09-check.py --run      # 사전 점검 통과 시 2회 호출 + DB 대조 + 영수증 저장
  --force: 사전 점검 실패여도 호출 (원인 재확인용)

영수증: develop/wonmin/runs/live-integration-qa-<UTC시각>.json (기존 FAIL 영수증은 덮어쓰지 않음)
"""
import argparse, base64, json, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TERM = ROOT / "tools/vm_web_terminal.py"
RUNS = ROOT / "develop/wonmin/runs"
WF_ID = "okeHandoffFlow01"
EXPECTED_NODES = 30  # main workflows/oke-handoff.json 기준


def load_env():
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("\"'")
    return env


def vm(cmd, timeout=90):
    r = subprocess.run([sys.executable, str(TERM), "run", cmd, "--timeout", str(timeout)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0 and not r.stdout.strip():
        raise RuntimeError(f"VM 명령 실패: {r.stderr.strip()[-300:]}")
    return r.stdout.strip()


def sql(q):
    b = base64.b64encode(q.encode()).decode()
    out = vm(f"echo {b} | base64 -d | docker exec -i -e PGPASSWORD=postgres oke-postgres-1 "
             f"psql -U postgres -d postgres -At -F '|'", 60)
    return [l for l in out.splitlines() if l.strip()]


def counts():
    t, a, d = sql("select (select count(*) from app.tickets),(select count(*) from app.alerts),"
                  "(select count(*) from app.dlq);")[-1].split("|")
    return {"tickets": int(t), "alerts": int(a), "dlq": int(d)}


def preflight():
    """VM 게시본을 읽기 전용으로 내보내 구조만 확인한다."""
    raw = vm(f"docker exec oke-n8n-1 n8n export:workflow --id={WF_ID} 2>/dev/null | base64 -w0")
    w = json.loads(base64.b64decode(raw.splitlines()[-1]))
    w = w[0] if isinstance(w, list) else w
    names = {n["name"]: n for n in w["nodes"]}
    hook = names.get("H01 Handoff Webhook", {})
    targeted = {x["node"] for c in w["connections"].values() for o in c.get("main", []) for x in o}
    checks = {
        "active": w.get("active") is True,
        "node_count_30": len(w["nodes"]) == EXPECTED_NODES,
        "h01_webhook_present": bool(hook),
        "h01_path_oke_handoff": hook.get("parameters", {}).get("path") == "oke-handoff",
        "h01_connected_to_h02": "H02 Validate and Map" in targeted,
        "error_workflow_set": bool(w.get("settings", {}).get("errorWorkflow")),
    }
    info = {"workflow_id": WF_ID, "updatedAt": w.get("updatedAt"), "versionId": w.get("versionId"),
            "nodes": len(w["nodes"]), "errorWorkflow": w.get("settings", {}).get("errorWorkflow")}
    # errorWorkflow 미설정은 WF-09 호출 자체를 막지 않으므로 경고로만 둔다.
    blocking = [k for k, v in checks.items() if not v and k != "error_workflow_set"]
    return {"checks": checks, "info": info, "blocking": blocking, "pass": not blocking}


def send(n8n, key, payload):
    req = urllib.request.Request(f"{n8n}/webhook/oke-handoff",
                                 data=json.dumps(payload, ensure_ascii=False).encode(),
                                 headers={"Content-Type": "application/json", "X-Team-Key": key},
                                 method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            st, body = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        st, body = e.code, e.read().decode()
    try:
        body = json.loads(body)
    except ValueError:
        body = {"non_json_length": len(body)}
    return st, body, round(time.time() - t0, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="실제 handoff 2회 호출 (티켓 1건 생성)")
    ap.add_argument("--force", action="store_true", help="사전 점검 실패여도 호출")
    a = ap.parse_args()

    env = load_env()
    n8n, key = env["N8N_BASE"].rstrip("/"), env["TEAM_KEY"]
    pf = preflight()
    print("[사전 점검]", "PASS" if pf["pass"] else "FAIL", json.dumps(pf["info"], ensure_ascii=False))
    for k, v in pf["checks"].items():
        print(f"  {'OK ' if v else 'NG '} {k}")
    if not a.run:
        print("사전 점검만 수행했습니다. 실제 시험은 --run을 붙이세요.")
        return 0 if pf["pass"] else 1
    if not pf["pass"] and not a.force:
        print("사전 점검 실패로 호출하지 않았습니다(", ", ".join(pf["blocking"]), "). 재배포 후 다시 실행하세요.")
        return 1

    rid = f"wf09-idem-{int(time.time())}"
    payload = {"request_id": rid, "requester": "이준호", "user_id": "emp01",
               "question": "VPN 인증서 만료로 인한 재발급 긴급 요청",
               "title": "VPN 인증서 재발급 요청 (QA 멱등성 재시험)",
               "summary": "VPN 인증서 만료로 인한 재발급 이관",
               "category": "network", "priority": "high", "reason": "no_evidence"}
    before = counts()
    s1, b1, e1 = send(n8n, key, payload)
    mid = counts()
    s2, b2, e2 = send(n8n, key, payload)
    after = counts()

    tk = lambda b: b.get("ticket") if isinstance(b.get("ticket"), dict) else {}
    t1, t2 = tk(b1).get("ticket_id"), tk(b2).get("ticket_id")
    rows = sql(f"select ticket_id,request_key,status,priority,created_at from app.tickets "
               f"where request_key='{rid}';")
    alerts = sql(f"select count(*) from app.alerts where event_key like '{rid}%';")
    dlq = sql(f"select count(*) from app.dlq where request_id='{rid}';")
    d1 = {k: mid[k] - before[k] for k in before}
    d2 = {k: after[k] - mid[k] for k in before}
    checks = {
        "first_http_2xx": 200 <= s1 < 300,
        "second_http_2xx": 200 <= s2 < 300,
        "first_duplicate_false": tk(b1).get("duplicate") is False,
        "second_duplicate_true": tk(b2).get("duplicate") is True,
        "same_ticket_id": bool(t1) and t1 == t2,
        "db_one_ticket_for_request_key": len(rows) == 1,
        "second_call_no_new_ticket": d2["tickets"] == 0,
    }
    verdict = "PASS_WF09" if all(checks.values()) else "FAIL_WF09"
    rep = {
        "schema": "wonmin-live-wf09-v1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target": n8n, "request_id": rid, "verdict": verdict, "checks": checks,
        "preflight": pf,
        "first_call": {"http_status": s1, "elapsed_s": e1, "body": b1},
        "second_call": {"http_status": s2, "elapsed_s": e2, "body": b2},
        "db_counts": {"before": before, "after_first": mid, "after_second": after,
                      "delta_first": d1, "delta_second": d2},
        "db_ticket_rows_for_request_key": rows,
        "db_alert_rows_for_request": alerts[-1] if alerts else None,
        "db_dlq_rows_for_request": dlq[-1] if dlq else None,
        "previous_receipt": "runs/live-integration-qa-20261107.json (FAIL_LIVE_HANDOFF_500)",
        "secrets_included": False,
    }
    out = RUNS / f"live-integration-qa-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    text = json.dumps(rep, ensure_ascii=False, indent=2) + "\n"
    if any(s and s in text for s in (key, env.get("VM_PASSWORD"), env.get("EMP_PASS"), env.get("ADM_PASS"))):
        raise SystemExit("영수증에 비밀값이 포함되어 저장을 중단했습니다.")
    out.write_text(text, encoding="utf-8")
    print(f"[결과] {verdict}  1차={s1} {t1} dup={tk(b1).get('duplicate')}  "
          f"2차={s2} {t2} dup={tk(b2).get('duplicate')}  DB티켓행={len(rows)}  Δ1={d1} Δ2={d2}")
    for k, v in checks.items():
        print(f"  {'OK ' if v else 'NG '} {k}")
    print("영수증:", out.relative_to(ROOT))
    return 0 if verdict == "PASS_WF09" else 1


if __name__ == "__main__":
    sys.exit(main())
