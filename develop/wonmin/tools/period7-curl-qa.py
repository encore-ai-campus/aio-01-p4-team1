#!/usr/bin/env python3
"""Gated HTTPS runner for period-7 derived QA cases; never the official 14-case evaluator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from uuid import uuid4


OWN = Path(__file__).resolve().parents[1]
SUITE = OWN / "cases" / "period7-derived.json"
PRIVATE_ACCESS = Path("/Users/k5h00/port-cli/4pj 준비/orchestrator/private/VM-TEAM-ACCESS.txt")
PRIVATE_ENV = Path("/Users/k5h00/port-cli/4pj 준비/vm_deploy/.env")
ORIGIN = "https://aio-t1.isitsoft.kr:5678"
WEBHOOK_PATH = "/webhook/oke-support"
MAX_SECONDS = 20
ROUTES = {"자동 답변", "보완 질문", "담당자 이관", "권한 없음", "차단"}
DOC_IDS = {"password-policy", "remote-work-vpn", "email-and-documents", "device-issue-return",
           "software-usage", "security-incident", "meeting-room", "privacy"}


class NotRunnable(RuntimeError):
    pass


def read_private_value(*labels: str) -> str:
    """Find an explicitly labelled value without printing it; accept key=value or key: value."""
    if not PRIVATE_ACCESS.is_file():
        raise NotRunnable("private_handoff_missing")
    accepted = {label.casefold() for label in labels}
    matches: list[str] = []
    for line in PRIVATE_ACCESS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^\s*([^:=]+)\s*[:=]\s*(.*?)\s*$", line)
        if match and match.group(1).strip().casefold() in accepted:
            matches.append(match.group(2))
    if len(matches) == 1 and matches[0]:
        return matches[0]
    if len(matches) > 1:
        raise NotRunnable("private_handoff_credential_ambiguous")
    if not PRIVATE_ENV.is_file():
        raise NotRunnable("private_webhook_key_missing")
    env_values = []
    for line in PRIVATE_ENV.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*VM_TEAM_KEY\s*=\s*(.*?)\s*$", line)
        if match and match.group(1):
            env_values.append(match.group(1).strip().strip("\"'"))
    if len(env_values) != 1 or not env_values[0]:
        raise NotRunnable("private_webhook_key_missing_or_ambiguous")
    return env_values[0]


def validate_output_path(path: Path) -> Path:
    output = path.resolve()
    runs = (OWN / "runs").resolve()
    if not output.is_relative_to(runs) or output.exists() or output.suffix != ".json":
        raise NotRunnable("report_must_be_new_json_under_wonmin_runs")
    if not output.parent.is_dir() or not os.access(output.parent, os.W_OK):
        raise NotRunnable("report_directory_unavailable")
    return output


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(131072), b""):
            digest.update(chunk)
    return digest.hexdigest()


def curl_transport_kind(returncode: int) -> str:
    if returncode == 28:
        return "timeout"
    if returncode in {35, 51, 58, 60, 77, 90}:
        return "tls"
    return "network_or_curl_error"


def is_baseline_access_failure(status: int) -> bool:
    return status in {0, 403, 404}


def curl_post(body: dict, team_key: str) -> tuple[int, object, float]:
    if "\n" in team_key or "\r" in team_key:
        raise NotRunnable("private_webhook_key_invalid")
    with tempfile.TemporaryDirectory(prefix="p7-qa-") as temp:
        os.chmod(temp, 0o700)
        root = Path(temp)
        request_file, response_file, config_file = (root / "request.json", root / "response.json", root / "curl.conf")
        request_file.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        config_file.write_text("header = \"X-Team-Key: " + team_key.replace("\\", "\\\\").replace('"', '\\"') + "\"\n",
                               encoding="utf-8")
        for path in (request_file, config_file):
            os.chmod(path, 0o600)
        fd = os.open(response_file, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)
        os.chmod(response_file, 0o600)
        args = ["curl", "--silent", "--show-error", "--proto", "=https", "--tlsv1.2",
                "--connect-timeout", "4", "--max-time", str(MAX_SECONDS), "--config", str(config_file),
                "--header", "Content-Type: application/json", "--data-binary", "@" + str(request_file),
                "--output", str(response_file), "--write-out", "%{http_code}", ORIGIN + WEBHOOK_PATH]
        started = time.monotonic()
        try:
            result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, timeout=MAX_SECONDS + 2,
                                    check=False, env={k: v for k, v in os.environ.items()
                                                      if k not in {"FLOW_WEBHOOK_KEY", "X_TEAM_KEY", "VM_TEAM_KEY"}})
        except subprocess.TimeoutExpired:
            return 0, {"transport": "timeout"}, round(time.monotonic() - started, 3)
        elapsed = round(time.monotonic() - started, 3)
        if result.returncode:
            return 0, {"transport": curl_transport_kind(result.returncode), "curl_exit": result.returncode}, elapsed
        if not result.stdout.isdigit():
            return 0, {"transport": "invalid_status"}, elapsed
        status = int(result.stdout)
        try:
            raw = response_file.read_bytes()
            parsed = json.loads(raw) if raw else None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
        return status, parsed, elapsed


def safe_summary(case_id: str, request_id: str, status: int, payload: object,
                 elapsed: float, case: dict, call_index: int) -> dict:
    expected = case.get("expect", {})
    result = {"case_id": case_id, "call_index": call_index, "request_id": request_id,
              "http_status": status, "elapsed_seconds": elapsed, "observed": {},
              "checks": {}, "unobserved": []}
    if not isinstance(payload, dict):
        result["observed"] = {"response_shape": "non_json_or_non_object"}
        result["verdict"] = "FAIL_OR_INCOMPLETE"
        return result
    if isinstance(payload.get("transport"), str):
        result["observed"] = {"transport": payload["transport"],
                              "curl_exit": payload.get("curl_exit")}
        result["verdict"] = "FAIL_OR_INCOMPLETE"
        return result
    sources = payload.get("sources")
    ticket = payload.get("ticket")
    echoed_id = payload.get("request_id")
    route = payload.get("route")
    reason = payload.get("reason")
    ticket_id = ticket.get("ticket_id") if isinstance(ticket, dict) else None
    result["observed"] = {
        "request_id_matches": echoed_id == request_id if status == 200 else None,
        "route": route if isinstance(route, str) and route in ROUTES
                 else ("unclassified_route" if isinstance(route, str) else None),
        "reason": reason if isinstance(reason, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", reason)
                  else ("unclassified_reason" if isinstance(reason, str) else None),
        "source_docs": [item.get("doc") if isinstance(item.get("doc"), str)
                        and item["doc"] in DOC_IDS
                        else "unclassified_doc" for item in sources if isinstance(item, dict)]
                        if isinstance(sources, list) else None,
        "ticket_id": ticket_id if isinstance(ticket_id, str) and re.fullmatch(r"T-\d+", ticket_id) else None,
        "ticket_duplicate": ticket.get("duplicate") if isinstance(ticket, dict)
                           and type(ticket.get("duplicate")) is bool else None,
        "security_masked": (payload.get("security", {}).get("masked")
                            if isinstance(payload.get("security"), dict)
                            and type(payload["security"].get("masked")) is int else None),
    }
    checks = result["checks"]
    # A successful common response must echo the unique request ID; validation errors may not.
    if status == 200:
        checks["request_id_matches"] = echoed_id == request_id
    if "http_status" in expected:
        checks["http_status"] = status == expected["http_status"]
    if "http_status_in" in expected:
        checks["http_status"] = status in expected["http_status_in"]
    if "route" in expected:
        checks["route"] = result["observed"]["route"] == expected["route"]
    if "route_if_200" in expected:
        checks["route"] = status == 200 and result["observed"]["route"] == expected["route_if_200"]
    if "route_in" in expected:
        checks["route"] = result["observed"]["route"] in expected["route_in"]
    if "source_doc" in expected:
        checks["source_doc"] = expected["source_doc"] in (result["observed"]["source_docs"] or [])
    if expected.get("sources_empty"):
        checks["sources_empty"] = result["observed"]["source_docs"] == []
    if "ticket" in expected:
        checks["ticket_null"] = (ticket is None) == (expected["ticket"] is None)
    if expected.get("ticket_required"):
        checks["ticket_present"] = bool(result["observed"]["ticket_id"])
    if expected.get("ticket_required_if_handoff"):
        checks["handoff_ticket_present"] = (bool(result["observed"]["ticket_id"])
                                              if result["observed"]["route"] == "담당자 이관"
                                              else ticket is None if result["observed"]["route"] == "권한 없음"
                                              else False)
    if expected.get("first_duplicate") is not None and call_index == 1:
        checks["ticket_duplicate"] = result["observed"]["ticket_duplicate"] is expected["first_duplicate"]
    if expected.get("duplicate_on_second") is not None and call_index == 2:
        checks["ticket_duplicate"] = result["observed"]["ticket_duplicate"] is expected["duplicate_on_second"]
    if expected.get("code"):
        error = payload.get("error")
        codes = payload.get("codes", error.get("codes") if isinstance(error, dict) else None)
        checks["error_code"] = expected["code"] in codes if isinstance(codes, list) else False
    if expected.get("masked_contact"):
        security = payload.get("security")
        checks["masked_count"] = (isinstance(security, dict) and type(security.get("masked")) is int
                                   and security["masked"] >= 1)
        answer = payload.get("answer")
        checks["answer_has_mask_token"] = (isinstance(answer, str)
                                            and ("****" in answer or "[마스킹]" in answer))
    if expected.get("no_other_ticket_details"):
        inspectable = json.dumps({key: payload.get(key) for key in ("answer", "ticket", "sources", "security")},
                                 ensure_ascii=False)
        checks["no_other_ticket_or_contact_details"] = (
            "T-1002" not in inspectable and
            not re.search(r"\b\d{2,4}[- ]?\d{3,4}[- ]?\d{4}\b|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", inspectable))
    if expected.get("no_it_source_or_text"):
        checks["no_it_source_reference"] = isinstance(sources, list) and all(
            not (isinstance(item, dict) and (item.get("access_level") == "it" or
                 (isinstance(item.get("doc"), str) and item["doc"].startswith("it-")))) for item in sources)
        result["unobserved"].extend(["answer content against protected document", "pre-search access-filter trace"])
    result["unobserved"].extend(case.get("unobserved_for_full_pass", []))
    result["unobserved"].extend(expected.get("unobserved_for_full_pass", []))
    if expected.get("only_one_ticket"):
        result["unobserved"].append("independent DB observation proves exactly one persisted ticket")
    result["unobserved"] = list(dict.fromkeys(result["unobserved"]))
    result["verdict"] = "PASS_OBSERVED_FIELDS" if checks and all(checks.values()) else "FAIL_OR_INCOMPLETE"
    if result["unobserved"] and result["verdict"].startswith("PASS"):
        result["verdict"] = "PARTIAL_UNOBSERVED"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", choices=("no_ticket_expected_candidates", "live_request_candidates", "team_five_categories"), required=True)
    parser.add_argument("--case", action="append", help="case ID; default is all selected cases")
    parser.add_argument("--execute-live-writes", action="store_true", help="requires controller deploy-ready gate")
    parser.add_argument("--output", type=Path, required=True, help="new private report path under develop/wonmin/runs")
    args = parser.parse_args()
    try:
        if not args.execute_live_writes:
            raise NotRunnable("execution_requires_explicit_live_flag")
        if os.environ.get("OKE_PERIOD7_DEPLOY_READY") != "1":
            raise NotRunnable("controller_deploy_ready_gate_missing")
        if os.environ.get("OKE_PERIOD7_WRITE_WINDOW") != "1":
            raise NotRunnable("controller_write_window_gate_missing")
        output = validate_output_path(args.output)
        deploy_sha = os.environ.get("OKE_PERIOD7_DEPLOY_SHA", "")
        if not re.fullmatch(r"[0-9a-f]{7,40}", deploy_sha, re.I):
            raise NotRunnable("controller_deploy_sha_missing_or_invalid")
        suite_hash = sha256(SUITE)
        runner_hash = sha256(Path(__file__).resolve())
        team_key = read_private_value("X_TEAM_KEY", "X-Team-Key", "FLOW_WEBHOOK_KEY")
        if "\n" in team_key or "\r" in team_key:
            raise NotRunnable("private_webhook_key_invalid")
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        if args.selection == "team_five_categories":
            cases = [{**case, "category": category["category"]}
                     for category in suite[args.selection] for case in category["cases"]]
        else:
            cases = list(suite[args.selection])
        cases = [case for case in cases if not args.case or case["id"] in args.case]
        if args.case and {case["id"] for case in cases} != set(args.case):
            raise NotRunnable("unknown_case_id")
        # Reserve and permission-check the report path before issuing any live request.
        with output.open("x", encoding="utf-8") as handle:
            handle.write('{"verdict":"RUNNING"}\n')
        os.chmod(output, 0o600)
        reports = []
        paired = {}
        abort_status = None
        for case in cases:
            count = case.get("calls", 1)
            request_id = "p7-" + uuid4().hex
            base_input = dict(case["input"])
            if "question_repeat_chars" in base_input:
                base_input["question"] = "x" * base_input.pop("question_repeat_chars")
            for call_index in range(1, count + 1):
                body = {"request_id": request_id, "channel": "web", **base_input}
                status, payload, elapsed = curl_post(body, team_key)
                current = safe_summary(case["id"], request_id, status, payload, elapsed,
                                       case, call_index)
                if case.get("category"):
                    current["category"] = case["category"]
                reports.append(current)
                paired.setdefault(case["id"], []).append(current)
                if is_baseline_access_failure(status):
                    abort_status = status
                    break
                if current["verdict"] == "FAIL_OR_INCOMPLETE":
                    break
            if abort_status is not None:
                break
        for case in cases:
            if case.get("expect", {}).get("same_ticket_id"):
                rows = paired.get(case["id"], [])
                ids = [row["observed"].get("ticket_id") for row in rows]
                matched = len(rows) == 2 and bool(ids[0]) and ids[0] == ids[1]
                for row in rows:
                    row["checks"]["same_ticket_id"] = matched
                    if not matched:
                        row["verdict"] = "FAIL_OR_INCOMPLETE"
        category_count = (len({case.get("category") for case in cases})
                          if args.selection == "team_five_categories" else None)
        with output.open("w", encoding="utf-8") as handle:
            json.dump({"scope": "derived_not_official_common_suite", "selection": args.selection,
                       "origin": ORIGIN, "deploy_sha": deploy_sha,
                       "suite_sha256": suite_hash, "runner_sha256": runner_hash,
                       "category_count": category_count, "aborted_on_baseline_failure": abort_status is not None,
                       "abort_http_status": abort_status, "cases": reports}, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.chmod(output, 0o600)
        print(json.dumps({"report": str(output), "category_count": category_count, "case_count": len(cases),
                          "request_count": len(reports), "aborted_on_baseline_failure": abort_status is not None,
                          "abort_http_status": abort_status, "verdicts":
                          {value: sum(row["verdict"] == value for row in reports)
                           for value in sorted({row["verdict"] for row in reports})}}, ensure_ascii=False))
        return 0
    except NotRunnable as error:
        print(json.dumps({"verdict": "NOT_RUN", "reason": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
