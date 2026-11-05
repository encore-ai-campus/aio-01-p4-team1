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
      $: nodeName => ({first: () => ({json: outputs[nodeName]})})
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
  const execute = (name, value, allItems) => {
    const items = vm.runInNewContext('(function(){' + nodes[name].parameters.jsCode + '})()', {
      $input: {first: () => ({json: value}), all: () => allItems.map(json => ({json}))},
      $: nodeName => ({first: () => ({json: outputs[nodeName]})})
    }, {timeout: 1000});
    if (!Array.isArray(items) || items.length !== 1 || !items[0].json) throw Error(test.id + ': invalid ' + name);
    let result = items[0].json;
    if (name === 'N09 Mock C03' && test.search_result) {
      const fixture = data.searchResults[test.search_result];
      if (!fixture) throw Error(test.id + ': unknown search result');
      result.search_http_status = fixture.status;
      result.search_raw = fixture.body;
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
    outputs[name] = result;
    return result;
  };
  let value = {body: test.body};
  for (const name of ['N02 Normalize input', 'N03 Validate employee MOCK', 'N04 Injection rules']) {
    value = execute(name, value, []);
  }
  if (value.codes.length || value.employee_lookup !== 'ok' || value.blocked === true) {
    value = execute('N22 Finalize P0-3', value, []);
  } else {
    for (const name of ['N06 Triage MOCK', 'N06 Parse triage', 'N07 Route triage', 'N08 Build search input']) {
      value = execute(name, value, []);
    }
    const base = value;
    let search = base;
    for (const name of ['N09 Mock C03', 'N09 Normalize search']) search = execute(name, search, []);
    let ticket = base;
    for (const name of ['N10 Build ticket lookup', 'N10 Mock ticket', 'N10 Normalize ticket']) ticket = execute(name, ticket, []);
    value = execute('N11 Join retrieval', null, [search, ticket]);
    value = execute('N12 Evidence gate', value, []);
    value = execute('N20 Prepare handoff', value, []);
    if (value.handoff_needed) {
      value = execute('N20 Mock C04', value, []);
      value = execute('N20 Map handoff', value, []);
    }
    value = execute('N22 Finalize P0-3', value, []);
  }
  results.push({id: test.id, final: value, searchRequest: outputs['N08 Build search input']?.search_request ?? null,
    search: outputs['N09 Normalize search']?.search ?? null,
    lookupRequest: outputs['N10 Build ticket lookup']?.lookup_request ?? null,
    ticketLookup: outputs['N10 Normalize ticket']?.ticket_lookup ?? null,
    maskCount: outputs['N10 Normalize ticket']?.mask_count ?? null,
    retrievalReason: outputs['N12 Evidence gate']?.retrieval_reason ?? null,
    retrievalDecision: outputs['N12 Evidence gate']?.retrieval_decision ?? null,
    handoffPayload: outputs['N20 Prepare handoff']?.handoff_payload ?? null,
    handoffState: outputs['N20 Map handoff']?.handoff?.state ?? null,
    usableEvidence: outputs['N12 Evidence gate']?.usable_evidence ?? null});
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
    if any(name in names for name in TICKET_CHAIN) and not has_ticket:
        raise ValueError("incomplete ticket lookup chain")
    expected_next = "N11 Collect retrieval" if has_merge else "N10 Build ticket lookup" if has_ticket else "N20 Prepare handoff"
    if flow["connections"].get("N09 Normalize search", {}).get("main") != [[{"node": expected_next, "type": "main", "index": 0}]]:
        raise ValueError("search normalization connection changed")
    if has_ticket:
        for source, target in zip(TICKET_CHAIN[:-1], TICKET_CHAIN[1:]):
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
            {"node": "N09 Mock C03", "type": "main", "index": 0},
            {"node": "N10 Build ticket lookup", "type": "main", "index": 0}]]:
            raise ValueError("retrieval branches changed")
        for source, target in (("N11 Collect retrieval", "N11 Join retrieval"),
                               ("N11 Join retrieval", "N12 Evidence gate"),
                               ("N12 Evidence gate", "N20 Prepare handoff")):
            if flow["connections"].get(source, {}).get("main") != [[{"node": target, "type": "main", "index": 0}]]:
                raise ValueError(f"retrieval connection changed: {source}")
    if any(node["type"] == "n8n-nodes-base.httpRequest" for node in nodes):
        raise ValueError("this local Mock snapshot must not send HTTP requests")
    return True


def run(flow, cases, container):
    tests = [{"id": case["id"], "body": read(ROOT / case["request_file"]),
              "search_result": case.get("search_result"), "lookup_result": case.get("lookup_result"),
              "handoff_result": case.get("handoff_result")}
             for case in cases]
    has_ticket = all(name in {node["name"] for node in flow["nodes"]} for name in TICKET_CHAIN)
    has_merge = "N11 Collect retrieval" in {node["name"] for node in flow["nodes"]}
    payload = json.dumps({"flow": flow, "chain": BASE_CHAIN + (TICKET_CHAIN if has_ticket else []) + TAIL,
                          "tests": tests, "searchResults": read(ROOT / "fixtures/search-results.json")["results"],
                          "ticketResults": read(ROOT / "fixtures/ticket-lookups.json")["results"] if has_ticket else {},
                          "handoffResults": read(ROOT / "fixtures/c04-wonmin-samples.json")["results"] if has_merge else {}},
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
    parser.add_argument("workflow", nargs="?", default="workflows/oke-support-04.json")
    parser.add_argument("cases", nargs="?", default="cases/support-search.json")
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
