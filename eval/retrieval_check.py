#!/usr/bin/env python3
"""Local P1-1 Mock checker; it does not call n8n, C03, or ticket APIs."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_CHAIN = [
    "N02 Normalize input", "N03 Validate employee MOCK", "N04 Injection rules",
    "N06 Triage MOCK", "N06 Parse triage", "N07 Route triage",
    "N08 Build search input", "N09 Mock C03", "N09 Normalize search",
]
TICKET_CHAIN = ["N10 Build ticket lookup", "N10 Mock ticket", "N10 Normalize ticket"]
TAIL = ["N20 Prepare handoff", "N20 Mock C04", "N20 Map handoff", "N22 Finalize P0-3"]
RUNNER = r"""
const fs = require('fs'), vm = require('vm');
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
const nodes = Object.fromEntries(data.flow.nodes.map(node => [node.name, node]));
const results = [];
for (const test of data.tests) {
  let value = {body: test.body};
  const outputs = {};
  for (const name of data.chain) {
    const skipOnGate = !['N02 Normalize input', 'N03 Validate employee MOCK',
      'N04 Injection rules', 'N22 Finalize P0-3'].includes(name);
    if (skipOnGate && (value.codes.length || value.employee_lookup !== 'ok' || value.blocked === true)) continue;
    if (['N20 Mock C04', 'N20 Map handoff'].includes(name) && value.handoff_needed !== true) continue;
    const inputValue = value;
    const items = vm.runInNewContext('(function(){' + nodes[name].parameters.jsCode + '})()', {
      $input: {first: () => ({json: inputValue})},
      $: nodeName => ({first: () => ({json: outputs[nodeName]})}),
      $env: {SERVICE_MODE: 'mock', DATA_API_URL: 'http://data-api:8800'}
    }, {timeout: 1000});
    if (!Array.isArray(items) || items.length !== 1 || !items[0].json) throw Error(test.id + ': invalid ' + name);
    value = items[0].json;
    if (name === 'N09 Mock C03' && test.search_result) {
      const fixture = data.searchResults[test.search_result];
      if (!fixture) throw Error(test.id + ': unknown search result');
      value.search_http_status = fixture.status;
      value.search_raw = fixture.body;
    }
    if (name === 'N10 Mock ticket' && test.lookup_result) {
      const fixture = data.ticketResults[test.lookup_result];
      if (!fixture) throw Error(test.id + ': unknown ticket result');
      value.lookup_http_status = fixture.status;
      value.lookup_raw = fixture.body ?? {error: fixture.transport_error};
    }
    outputs[name] = value;
  }
  results.push({id: test.id, final: value, searchRequest: outputs['N08 Build search input']?.search_request ?? null,
    search: outputs['N09 Normalize search']?.search ?? null,
    lookupRequest: outputs['N10 Build ticket lookup']?.lookup_request ?? null,
    ticketLookup: outputs['N10 Normalize ticket']?.ticket_lookup ?? null,
    maskCount: outputs['N10 Normalize ticket']?.mask_count ?? null});
}
process.stdout.write(JSON.stringify(results));
"""
PARALLEL_RUNNER = r"""
const fs = require('fs'), vm = require('vm');
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
const nodes = Object.fromEntries(data.flow.nodes.map(node => [node.name, node]));
const results = [];
for (const test of data.tests) {
  const outputs = {};
  let handoffCalls = 0;
  const execute = (name, value, allItems) => {
    const items = vm.runInNewContext('(function(){' + nodes[name].parameters.jsCode + '})()', {
      $input: {first: () => ({json: value}), all: () => allItems.map(json => ({json}))},
      $: nodeName => ({first: () => ({json: outputs[nodeName]})}),
      $env: {SERVICE_MODE: 'mock', DATA_API_URL: 'http://data-api:8800'}
    }, {timeout: 1000});
    if (!Array.isArray(items) || items.length !== 1 || !items[0].json) throw Error(test.id + ': invalid ' + name);
    let result = items[0].json;
    if (name === 'N09 Mock C03' && test.search_result) {
      const fixture = data.searchResults[test.search_result];
      if (!fixture) throw Error(test.id + ': unknown search result');
      result.search_http_status = fixture.status;
      result.search_raw = fixture.body;
    }
    if (name === 'N05 Replay MOCK' && test.replay_result) {
      const fixture = data.replayResults[test.replay_result];
      if (!fixture) throw Error(test.id + ': unknown replay result');
      result.replay_http_status = fixture.status;
      result.replay_raw = fixture.body;
    }
    if (name === 'N10 Mock ticket' && test.lookup_result) {
      const fixture = data.ticketResults[test.lookup_result];
      if (!fixture) throw Error(test.id + ': unknown ticket result');
      result.lookup_http_status = fixture.status;
      result.lookup_raw = fixture.body ?? {error: fixture.transport_error};
    }
    if (name === 'N20 Mock C04' && test.handoff_result) {
      const fixture = data.handoffResults[test.handoff_result];
      if (!fixture) throw Error(test.id + ': unknown handoff result');
      result.handoff_status = fixture.status;
      result.handoff_response = fixture.body;
    }
    if (name === 'N20 Mock C04') handoffCalls++;
    if (name === 'N06 Triage MOCK' && test.triage_error) result.error = test.triage_error;
    if (name === 'N13 Writer MOCK' && test.writer_result) {
      const fixture = data.writerResults[test.writer_result];
      if (!fixture) throw Error(test.id + ': unknown writer result');
      result.writer_output = fixture.output;
      if (fixture.error) result.error = fixture.error;
    }
    if (name === 'N14 Verifier MOCK' && test.verifier_result) {
      const fixture = data.verifierResults[test.verifier_result];
      if (!fixture) throw Error(test.id + ': unknown verifier result');
      result.verifier_output = fixture.output;
      if (fixture.error) result.error = fixture.error;
    }
    outputs[name] = result;
    return result;
  };
  let value = {body: test.body};
  for (const name of ['N02 Normalize input', 'N03 Validate employee MOCK', 'N04 Injection rules']) {
    value = execute(name, value, []);
  }
  if (nodes['N05 Replay MOCK']) {
    value = execute('N05 Replay MOCK', value, []);
    value = execute('N05 Parse replay', value, []);
  }
  if (value.codes.length || value.employee_lookup !== 'ok' || value.blocked === true || value.replay_terminal === true) {
    value = execute('N22 Finalize P0-3', value, []);
  } else {
    for (const name of ['N06 Triage MOCK', 'N06 Parse triage', 'N07 Route triage']) {
      value = execute(name, value, []);
    }
    if (nodes['N07 Route urgent'] && value.urgent_pre_handoff === true) {
      for (const name of ['N20 Prepare handoff', 'N20 Mock C04', 'N20 Map handoff']) {
        value = execute(name, value, []);
      }
    }
    value = execute('N08 Build search input', value, []);
    const base = value;
    let search = base;
    for (const name of ['N09 Mock C03', 'N09 Normalize search']) search = execute(name, search, []);
    let ticket = base;
    for (const name of ['N10 Build ticket lookup', 'N10 Mock ticket', 'N10 Normalize ticket']) ticket = execute(name, ticket, []);
    value = execute('N11 Join retrieval', null, [search, ticket]);
    value = execute('N12 Evidence gate', value, []);
    if (nodes['N13 Prepare writer'] && value.retrieval_decision === 'write') {
      for (const name of ['N13 Prepare writer', 'N13 Writer MOCK', 'N13 Parse writer']) value = execute(name, value, []);
      if (value.writer_valid) {
        for (const name of ['N14 Prepare verifier', 'N14 Verifier MOCK', 'N14 Parse verifier',
                            'N15 Decide answer']) value = execute(name, value, []);
      }
    }
    if (!value.handoff_done) {
      value = execute('N20 Prepare handoff', value, []);
      if (value.handoff_needed) {
        value = execute('N20 Mock C04', value, []);
        value = execute('N20 Map handoff', value, []);
      }
    }
    value = execute('N22 Finalize P0-3', value, []);
  }
  if (nodes['N22 Output filter']) value = execute('N22 Output filter', value, []);
  results.push({id: test.id, final: value, searchRequest: outputs['N08 Build search input']?.search_request ?? null,
    search: outputs['N09 Normalize search']?.search ?? null,
    lookupRequest: outputs['N10 Build ticket lookup']?.lookup_request ?? null,
    ticketLookup: outputs['N10 Normalize ticket']?.ticket_lookup ?? null,
    maskCount: outputs['N10 Normalize ticket']?.mask_count ?? null,
    retrievalReason: outputs['N12 Evidence gate']?.retrieval_reason ?? null,
    retrievalDecision: outputs['N12 Evidence gate']?.retrieval_decision ?? null,
    handoffPayload: outputs['N20 Prepare handoff']?.handoff_payload ?? null,
    handoffState: outputs['N20 Map handoff']?.handoff?.state ?? null,
    usableEvidence: outputs['N12 Evidence gate']?.usable_evidence ?? null,
    writerValid: outputs['N13 Parse writer']?.writer_valid ?? null,
    verifierValid: outputs['N14 Parse verifier']?.verifier_valid ?? null,
    verificationFailure: outputs['N14 Parse verifier']?.verification_failure ??
      outputs['N13 Parse writer']?.verification_failure ?? null,
    writerInput: outputs['N13 Prepare writer']?.writer_input ?? null,
    handoffCalls,
    replayState: outputs['N05 Parse replay']?.replay_state ?? null,
    triageRan: Boolean(outputs['N06 Triage MOCK']),
    searchRan: Boolean(outputs['N09 Mock C03'])});
}
process.stdout.write(JSON.stringify(results));
"""


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check(flow):
    nodes = flow["nodes"]
    names = {node["name"] for node in nodes}
    if len(names) != len(nodes) or flow.get("name") != "oke-support":
        raise ValueError("workflow name or node names are invalid")
    webhook = next(node for node in nodes if node["name"] == "N01 Support webhook")
    if webhook["parameters"].get("path") != "oke-support" or webhook["parameters"].get("authentication") != "headerAuth":
        raise ValueError("support webhook path/authentication changed")
    if len([node for node in nodes if node["type"] == "n8n-nodes-base.respondToWebhook"]) != 1:
        raise ValueError("expected one Respond node")
    for source, ports in flow["connections"].items():
        if source not in names:
            raise ValueError(f"unknown source node: {source}")
        for branches in ports.values():
            for branch in branches:
                for edge in branch:
                    if edge["node"] not in names:
                        raise ValueError(f"unknown target node: {edge['node']}")
    if any(name not in names for name in BASE_CHAIN + TAIL):
        raise ValueError("P1-1 search/triage/handoff node missing")
    has_ticket = all(name in names for name in TICKET_CHAIN)
    has_merge = "N11 Collect retrieval" in names
    has_verification = "N13 Prepare writer" in names
    has_urgent = "N07 Route urgent" in names
    has_replay = "N05 Replay MOCK" in names
    has_http = "N03 Get employees HTTP" in names
    if any(name in names for name in TICKET_CHAIN) and not has_ticket:
        raise ValueError("incomplete ticket lookup chain")
    expected_next = "N11 Collect retrieval" if has_merge else "N10 Build ticket lookup" if has_ticket else "N20 Prepare handoff"
    if flow["connections"].get("N09 Normalize search", {}).get("main") != [[{"node": expected_next, "type": "main", "index": 0}]]:
        raise ValueError("search normalization connection changed")
    if has_ticket:
        for source, target in zip(TICKET_CHAIN[:-1], TICKET_CHAIN[1:]):
            if has_http and source == "N10 Build ticket lookup":
                target = "N10 Ticket mode"
            if flow["connections"].get(source, {}).get("main") != [[{"node": target, "type": "main", "index": 0}]]:
                raise ValueError(f"ticket lookup connection changed: {source}")
        target = "N11 Collect retrieval" if has_merge else "N20 Prepare handoff"
        index = 1 if has_merge else 0
        if flow["connections"].get(TICKET_CHAIN[-1], {}).get("main") != [[{"node": target, "type": "main", "index": index}]]:
            raise ValueError("ticket lookup terminal connection changed")
    if has_merge:
        if not all(name in names for name in ("N11 Join retrieval", "N12 Evidence gate")):
            raise ValueError("incomplete retrieval merge")
        if flow["connections"].get("N08 Build search input", {}).get("main") != [[
            {"node": "N09 Search mode" if has_http else "N09 Mock C03", "type": "main", "index": 0},
            {"node": "N10 Build ticket lookup", "type": "main", "index": 0}]]:
            raise ValueError("retrieval branches changed")
        for source, target in (("N11 Collect retrieval", "N11 Join retrieval"),
                               ("N11 Join retrieval", "N12 Evidence gate")):
            if flow["connections"].get(source, {}).get("main") != [[{"node": target, "type": "main", "index": 0}]]:
                raise ValueError(f"retrieval connection changed: {source}")
        target = "N12 Route evidence" if has_verification else "N20 Prepare handoff"
        if flow["connections"].get("N12 Evidence gate", {}).get("main") != [[{"node": target, "type": "main", "index": 0}]]:
            raise ValueError("retrieval gate connection changed")
    if has_verification:
        required = {"N12 Route evidence", "N13 Writer mode", "N13 Writer MOCK", "N13 Writer Agent",
                    "N13 Writer model", "N13 Parse writer", "N13 Writer valid", "N14 Prepare verifier",
                    "N14 Verifier mode", "N14 Verifier MOCK", "N14 Verifier Agent", "N14 Verifier model",
                    "N14 Parse verifier", "N15 Decide answer", "N15 Route answer"}
        if not required <= names:
            raise ValueError("P1-2 writer/verifier chain incomplete")
        if "N22 Output filter" not in names:
            raise ValueError("P1-2 final output filter missing")
        if flow["connections"].get("N22 Finalize P0-3", {}).get("main") != [[
            {"node": "N22 Output filter", "type": "main", "index": 0}]]:
            raise ValueError("P1-2 final output connection missing")
        next_failure = "N21 Already handed off" if has_urgent else "N20 Prepare handoff"
        expected_routes = {
            "N12 Route evidence": ("N13 Prepare writer", next_failure),
            "N13 Writer mode": ("N13 Writer MOCK", "N13 Writer Agent"),
            "N13 Writer valid": ("N14 Prepare verifier", next_failure),
            "N14 Verifier mode": ("N14 Verifier MOCK", "N14 Verifier Agent"),
            "N15 Route answer": ("N22 Finalize P0-3", next_failure),
        }
        for source, targets in expected_routes.items():
            actual = flow["connections"].get(source, {}).get("main", [])
            if tuple(branch[0]["node"] for branch in actual if len(branch) == 1) != targets:
                raise ValueError(f"P1-2 route changed: {source}")
    if has_urgent:
        for source, target in (("N07 Route triage", "N07 Route urgent"),
                               ("N20 Map handoff", "N20 After handoff")):
            if flow["connections"].get(source, {}).get("main") != [[
                {"node": target, "type": "main", "index": 0}]]:
                raise ValueError(f"P1-3 priority connection changed: {source}")
        expected_routes = {
            "N07 Route urgent": ("N20 Prepare handoff", "N08 Build search input"),
            "N20 After handoff": ("N08 Build search input", "N22 Finalize P0-3"),
            "N21 Already handed off": ("N22 Finalize P0-3", "N20 Prepare handoff"),
        }
        for source, targets in expected_routes.items():
            actual = flow["connections"].get(source, {}).get("main", [])
            if tuple(branch[0]["node"] for branch in actual if len(branch) == 1) != targets:
                raise ValueError(f"P1-3 route changed: {source}")
    if has_replay:
        required = {"N05 Parse replay", "N05 Route replay"}
        if not required <= names:
            raise ValueError("P1-4 replay chain incomplete")
        for source, target in (("N04 Injection rules", "N05 Replay MOCK"),
                               ("N05 Replay MOCK", "N05 Parse replay"),
                               ("N05 Parse replay", "N05 Route replay")):
            if flow["connections"].get(source, {}).get("main") != [[
                {"node": target, "type": "main", "index": 0}]]:
                raise ValueError(f"P1-4 replay connection changed: {source}")
        actual = flow["connections"].get("N05 Route replay", {}).get("main", [])
        if tuple(branch[0]["node"] for branch in actual if len(branch) == 1) != (
                "N22 Finalize P0-3", "N05 Triage gate"):
            raise ValueError("P1-4 replay route changed")
        for model, agent in (("N13 Writer model", "N13 Writer Agent"),
                             ("N14 Verifier model", "N14 Verifier Agent")):
            if flow["connections"].get(model, {}).get("ai_languageModel") != [[
                {"node": agent, "type": "ai_languageModel", "index": 0}]]:
                raise ValueError(f"{model} not linked to its Agent")
    http_nodes = [node for node in nodes if node["type"] == "n8n-nodes-base.httpRequest"]
    if has_http:
        expected_http = {
            "N03 Get employees HTTP": ("GET", 2000),
            "N09 C03 HTTP": ("POST", 4000),
            "N10 Own ticket HTTP": ("GET", 2000),
            "N20 C04 HTTP": ("POST", 5000),
        }
        if {node["name"] for node in http_nodes} != set(expected_http):
            raise ValueError("P1-5 HTTP node set incomplete")
        for node in http_nodes:
            method, timeout = expected_http[node["name"]]
            p = node["parameters"]
            options = p.get("options", {})
            response = options.get("response", {}).get("response", {})
            if (p.get("method") != method or options.get("timeout") != timeout or
                    p.get("authentication") != "genericCredentialType" or
                    p.get("genericAuthType") != "httpHeaderAuth" or
                    not node.get("credentials", {}).get("httpHeaderAuth") or
                    not response.get("fullResponse") or not response.get("neverError") or
                    node.get("onError") != "continueRegularOutput"):
                raise ValueError(f"P1-5 HTTP settings invalid: {node['name']}")
        for source, target in (("N02 Normalize input", "N03 Employee mode"),
                               ("N03 Get employees HTTP", "N03 Capture employee"),
                               ("N03 Capture employee", "N04 Injection rules"),
                               ("N09 C03 HTTP", "N09 Capture C03"),
                               ("N09 Capture C03", "N09 Normalize search"),
                               ("N10 Build ticket lookup", "N10 Ticket mode"),
                               ("N10 Own ticket HTTP", "N10 Capture ticket"),
                               ("N10 Capture ticket", "N10 Normalize ticket"),
                               ("N20 C04 HTTP", "N20 Capture C04"),
                               ("N20 Capture C04", "N20 Map handoff")):
            if flow["connections"].get(source, {}).get("main") != [[
                {"node": target, "type": "main", "index": 0}]]:
                raise ValueError(f"P1-5 HTTP connection changed: {source}")
        expected_gates = {
            "N03 Employee mode": ("N03 Get employees HTTP", "N03 Validate employee MOCK"),
            "N09 Search mode": ("N09 C03 HTTP", "N09 Mock C03"),
            "N10 Ticket mode": ("N10 Own ticket HTTP", "N10 Mock ticket"),
            "N20 Handoff mode": ("N20 C04 HTTP", "N20 Mock C04"),
        }
        for source, targets in expected_gates.items():
            actual = flow["connections"].get(source, {}).get("main", [])
            if tuple(branch[0]["node"] for branch in actual if len(branch) == 1) != targets:
                raise ValueError(f"P1-5 HTTP gate changed: {source}")
    elif http_nodes:
        raise ValueError("unexpected HTTP node in Mock snapshot")
    return True


def run(flow, cases, container):
    tests = [{"id": case["id"], "body": read(ROOT / case["request_file"]),
              "search_result": case.get("search_result"), "lookup_result": case.get("lookup_result"),
              "handoff_result": case.get("handoff_result"), "writer_result": case.get("writer_result"),
              "verifier_result": case.get("verifier_result"), "triage_error": case.get("triage_error"),
              "replay_result": case.get("replay_result")}
             for case in cases]
    has_ticket = all(name in {node["name"] for node in flow["nodes"]} for name in TICKET_CHAIN)
    has_merge = "N11 Collect retrieval" in {node["name"] for node in flow["nodes"]}
    has_verification = "N13 Prepare writer" in {node["name"] for node in flow["nodes"]}
    has_replay = "N05 Replay MOCK" in {node["name"] for node in flow["nodes"]}
    payload = json.dumps({"flow": flow, "chain": BASE_CHAIN + (TICKET_CHAIN if has_ticket else []) + TAIL,
                          "tests": tests, "searchResults": read(ROOT / "eval/fixtures/search-results.json")["results"],
                          "ticketResults": read(ROOT / "eval/fixtures/ticket-lookups.json")["results"] if has_ticket else {},
                          "handoffResults": read(ROOT / "eval/fixtures/c04-wonmin-samples.json")["results"] if has_merge else {},
                          "writerResults": read(ROOT / "eval/fixtures/writer-results.json")["results"] if has_verification else {},
                          "verifierResults": read(ROOT / "eval/fixtures/verifier-results.json")["results"] if has_verification else {},
                          "replayResults": read(ROOT / "eval/fixtures/replay-results.json")["results"] if has_replay else {}},
                         ensure_ascii=False)
    if container:
        cmd = ["docker", "exec", "-i", container, "node", "-e", PARALLEL_RUNNER if has_merge else RUNNER]
    elif shutil.which("node"):
        cmd = ["node", "-e", PARALLEL_RUNNER if has_merge else RUNNER]
    else:
        raise RuntimeError("Node.js unavailable; supply --node-container")
    process = subprocess.run(cmd, input=payload, text=True, capture_output=True, check=False)
    if process.returncode:
        raise RuntimeError(process.stderr.strip())
    actuals = {row["id"]: row for row in json.loads(process.stdout)}
    failures = 0
    for case in cases:
        row, expected = actuals[case["id"]], case["expect"]
        final = row["final"]
        response = final["response"]
        problems = []
        if final["status_code"] != expected["http_status"]:
            problems.append("http_status")
        for key in ("route", "reason", "codes", "ticket"):
            if key in expected and response.get(key) != expected[key]:
                problems.append(key)
        if expected.get("ticket_present") and not isinstance(response.get("ticket"), dict):
            problems.append("ticket_present")
        if "search_state" in expected and (row["search"] or {}).get("state") != expected["search_state"]:
            problems.append("search_state")
        if expected.get("search_skipped") and row["search"] is not None:
            problems.append("search_skipped")
        if "lookup_state" in expected and (row["ticketLookup"] or {}).get("state") != expected["lookup_state"]:
            problems.append("lookup_state")
        if expected.get("lookup_request_absent") and row["lookupRequest"] is not None:
            problems.append("lookup_request_absent")
        for key, actual_key in (("lookup_requester", "requester"), ("lookup_ticket_id", "ticket_id")):
            if key in expected and (row["lookupRequest"] or {}).get(actual_key) != expected[key]:
                problems.append(key)
        if "mask_count" in expected and row["maskCount"] != expected["mask_count"]:
            problems.append("mask_count")
        if "security_masked" in expected and response.get("security", {}).get("masked") != expected["security_masked"]:
            problems.append("security_masked")
        if expected.get("evidence_redacted") and "support@example.invalid" in json.dumps(row.get("usableEvidence"), ensure_ascii=False):
            problems.append("evidence_redacted")
        for key in ("retrieval_reason", "retrieval_decision"):
            if key in expected and row[key.replace("retrieval_", "retrieval").replace("reason", "Reason").replace("decision", "Decision")] != expected[key]:
                problems.append(key)
        if "handoff_reason" in expected and (row.get("handoffPayload") or {}).get("reason") != expected["handoff_reason"]:
            problems.append("handoff_reason")
        if "handoff_state" in expected and row.get("handoffState") != expected["handoff_state"]:
            problems.append("handoff_state")
        if "duplicate" in expected and (response.get("ticket") or {}).get("duplicate") != expected["duplicate"]:
            problems.append("duplicate")
        if "ticket_id" in expected and (response.get("ticket") or {}).get("ticket_id") != expected["ticket_id"]:
            problems.append("ticket_id")
        for key, actual in (("writer_valid", "writerValid"), ("verifier_valid", "verifierValid"),
                            ("verification_failure", "verificationFailure")):
            if key in expected and row.get(actual) != expected[key]:
                problems.append(key)
        if "source_count" in expected and len(response.get("sources", [])) != expected["source_count"]:
            problems.append("source_count")
        if "handoff_calls" in expected and row.get("handoffCalls") != expected["handoff_calls"]:
            problems.append("handoff_calls")
        if "priority" in expected and (response.get("ticket") or {}).get("priority") != expected["priority"]:
            problems.append("priority")
        for key, actual in (("replay_state", "replayState"), ("triage_ran", "triageRan"),
                            ("search_ran", "searchRan")):
            if key in expected and row.get(actual) != expected[key]:
                problems.append(key)
        if "answer_contains" in expected and expected["answer_contains"] not in response.get("answer", ""):
            problems.append("answer_contains")
        if expected.get("answer_excludes") and expected["answer_excludes"] in response.get("answer", ""):
            problems.append("answer_excludes")
        if expected.get("writer_input_excludes") and expected["writer_input_excludes"] in json.dumps(row.get("writerInput"), ensure_ascii=False):
            problems.append("writer_input_excludes")
        if expected.get("contact_absent") and ("contact" in json.dumps(row["ticketLookup"], ensure_ascii=False) or
                                               "SHOULD_NOT_LEAK" in json.dumps(final, ensure_ascii=False)):
            problems.append("contact_absent")
        request = row["searchRequest"] or {}
        for key in ("access_levels", "top_k", "type"):
            if key in expected and request.get(key) != expected[key]:
                problems.append(key)
        if request and (request.get("request_id") != tests[cases.index(case)]["body"]["request_id"] or
                        tests[cases.index(case)]["body"]["question"] not in request.get("query", "")):
            problems.append("search_request_identity")
        if problems:
            failures += 1
            print(f"FAIL {case['id']}: {', '.join(problems)}")
        else:
            print(f"PASS {case['id']} (local Mock simulation)")
    print(f"local result: {len(cases)-failures}/{len(cases)}; no n8n/C03/ticket API calls")
    return failures == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", nargs="?", default="eval/workflows/oke-support-mock.json")
    parser.add_argument("cases", nargs="?", default="eval/support-retrieval.json")
    parser.add_argument("--node-container")
    args = parser.parse_args()
    try:
        flow = read(ROOT / args.workflow)
        check(flow)
        cases = read(ROOT / args.cases)["cases"]
        return 0 if run(flow, cases, args.node_container) else 1
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
