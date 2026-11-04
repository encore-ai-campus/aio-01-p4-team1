#!/usr/bin/env python3
"""Local P0-1/P0-2 checker for oke-support; not the evaluation-kit flow.py.

This tool checks the current Mock workflow and runs Code-node snippets with
Node.js. It does not import, publish, or call an n8n workflow.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P0_1_NODES = [
    "N01 Support webhook",
    "N02 Normalize input",
    "N03 Validate employee MOCK",
    "N04 Injection rules",
    "N22 Finalize P0-1",
    "N23 Respond",
]
REQUIRED_NODES = [
    "N01 Support webhook",
    "N02 Normalize input",
    "N03 Validate employee MOCK",
    "N04 Injection rules",
    "N05 Triage gate",
    "N05 Triage mode",
    "N06 Triage MOCK",
    "N06 Triage Agent",
    "N06 Triage model",
    "N06 Parse triage",
    "N07 Route triage",
    "N22 Finalize P0-2",
    "N23 Respond",
]
CODE_CHAIN = [
    "N02 Normalize input",
    "N03 Validate employee MOCK",
    "N04 Injection rules",
    "N06 Triage MOCK",
    "N06 Parse triage",
    "N07 Route triage",
    "N22 Finalize P0-2",
]
P0_1_CODE_CHAIN = P0_1_NODES[1:-1]
TRIAGE_CODE_NODES = set(CODE_CHAIN[3:6])
NODE_RUNNER = r"""
const fs = require('fs');
const vm = require('vm');
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
const nodes = Object.fromEntries(data.flow.nodes.map(node => [node.name, node]));
const result = [];
for (const test of data.tests) {
  let value = {body: test.body};
  const outputs = {};
  for (const name of data.codeChain) {
    if (data.triageCodeNodes.includes(name) &&
        (value.codes.length || value.employee_lookup !== 'ok' || value.blocked === true)) continue;
    const code = nodes[name].parameters.jsCode;
    const items = vm.runInNewContext('(function(){' + code + '})()', {
      $input: {first: () => ({json: value})},
      $: nodeName => ({first: () => ({json: outputs[nodeName]})})
    }, {timeout: 1000});
    if (!Array.isArray(items) || items.length !== 1 || !items[0].json) {
      throw new Error(test.id + ': invalid output from ' + name);
    }
    value = items[0].json;
    outputs[name] = value;
  }
  result.push({id: test.id, actual: value});
}
const parserResult = [];
for (const example of data.triageExamples) {
  const base = {clean_question: '접속이 안 돼요', context: '', request_id: 'parser-probe'};
  const input = {
    triage_mock: true,
    triage_output: example.raw_output ?? JSON.stringify(example.output)
  };
  const code = nodes['N06 Parse triage'].parameters.jsCode;
  const items = vm.runInNewContext('(function(){' + code + '})()', {
    $input: {first: () => ({json: input})},
    $: () => ({first: () => ({json: base})})
  }, {timeout: 1000});
  parserResult.push({id: example.id, actual_error: items[0].json.triage_error});
}
process.stdout.write(JSON.stringify({cases: result, parser: parserResult}));
"""


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def check_flow(path: Path):
    flow = load_json(path)
    nodes = flow["nodes"]
    by_name = {node["name"]: node for node in nodes}
    if len(by_name) != len(nodes):
        raise ValueError("duplicate node name")
    is_p0_1 = set(by_name) == set(P0_1_NODES)
    if not is_p0_1 and set(by_name) != set(REQUIRED_NODES):
        raise ValueError("node set differs from the P0-1 or P0-2 Mock workflow")
    if flow.get("name") != "oke-support":
        raise ValueError("workflow name must be oke-support")
    if flow.get("settings", {}).get("executionOrder") != "v1":
        raise ValueError("executionOrder must be v1")

    webhook = by_name["N01 Support webhook"]
    params = webhook["parameters"]
    for key, expected in (
        ("httpMethod", "POST"),
        ("path", "oke-support"),
        ("authentication", "headerAuth"),
        ("responseMode", "responseNode"),
    ):
        if params.get(key) != expected:
            raise ValueError(f"webhook {key} must be {expected}")
    if "httpHeaderAuth" not in webhook.get("credentials", {}):
        raise ValueError("Header Auth credential reference missing")
    if len([node for node in nodes if node["type"] == "n8n-nodes-base.respondToWebhook"]) != 1:
        raise ValueError("expected exactly one Respond node")
    if any(node["type"] == "n8n-nodes-base.httpRequest" for node in nodes):
        raise ValueError("P0 Mock workflow must not call a downstream service")

    fixture = load_json(ROOT / "fixtures/employees.json")
    employees = fixture["items"]
    if len(employees) != 6 or any(set(row) != {"name", "dept"} for row in employees):
        raise ValueError("employee fixture must contain six name/dept rows")
    mock_code = by_name["N03 Validate employee MOCK"]["parameters"]["jsCode"]
    for row in employees:
        if f"name: '{row['name']}', dept: '{row['dept']}'" not in mock_code:
            raise ValueError(f"workflow Mock differs from fixture: {row['name']}")

    if is_p0_1:
        if any("langchain" in node["type"] for node in nodes):
            raise ValueError("P0-1 must not have an LLM node")
        for source, target in zip(P0_1_NODES, P0_1_NODES[1:]):
            edges = flow.get("connections", {}).get(source, {}).get("main")
            if edges != [[{"node": target, "type": "main", "index": 0}]]:
                raise ValueError(f"expected P0-1 connection {source} -> {target}")
        if "N23 Respond" in flow.get("connections", {}):
            raise ValueError("Respond must be the terminal node")
        for name in P0_1_CODE_CHAIN:
            if by_name[name]["type"] != "n8n-nodes-base.code":
                raise ValueError(f"{name} must be a Code node")
        return flow

    expected_main = {
        "N01 Support webhook": [["N02 Normalize input"]],
        "N02 Normalize input": [["N03 Validate employee MOCK"]],
        "N03 Validate employee MOCK": [["N04 Injection rules"]],
        "N04 Injection rules": [["N05 Triage gate"]],
        "N05 Triage gate": [["N05 Triage mode"], ["N22 Finalize P0-2"]],
        "N05 Triage mode": [["N06 Triage MOCK"], ["N06 Triage Agent"]],
        "N06 Triage MOCK": [["N06 Parse triage"]],
        "N06 Triage Agent": [["N06 Parse triage"]],
        "N06 Parse triage": [["N07 Route triage"]],
        "N07 Route triage": [["N22 Finalize P0-2"]],
        "N22 Finalize P0-2": [["N23 Respond"]],
    }
    for source, branches in expected_main.items():
        actual = flow.get("connections", {}).get(source, {}).get("main")
        targets = [[edge["node"] for edge in branch] for branch in actual or []]
        if targets != branches:
            raise ValueError(f"unexpected connection from {source}: {targets}")
    model_edges = flow.get("connections", {}).get("N06 Triage model", {}).get("ai_languageModel")
    if model_edges != [[{"node": "N06 Triage Agent", "type": "ai_languageModel", "index": 0}]]:
        raise ValueError("triage Agent model connection missing")
    if "N23 Respond" in flow.get("connections", {}):
        raise ValueError("Respond must be the terminal node")
    for name in CODE_CHAIN:
        if by_name[name]["type"] != "n8n-nodes-base.code":
            raise ValueError(f"{name} must be a Code node")
    if by_name["N06 Triage Agent"]["type"] != "@n8n/n8n-nodes-langchain.agent":
        raise ValueError("triage Agent node missing")
    if "openAiApi" not in by_name["N06 Triage model"].get("credentials", {}):
        raise ValueError("triage model credential reference missing")

    examples = load_json(ROOT / "fixtures/triage-results.json")["examples"]
    if len(examples) < 3 or not any("expect_error" in row for row in examples):
        raise ValueError("triage fixture lacks normal and invalid schema examples")
    return flow


def run_local(flow, case_path: Path, container: str | None):
    cases = load_json(case_path)["cases"]
    tests = []
    for case in cases:
        request_file = ROOT / case["request_file"]
        tests.append({"id": case["id"], "body": load_json(request_file)})
    is_p0_1 = len(flow["nodes"]) == len(P0_1_NODES)
    triage_examples = [] if is_p0_1 else load_json(ROOT / "fixtures/triage-results.json")["examples"]
    payload = json.dumps(
        {"flow": flow, "tests": tests, "codeChain": P0_1_CODE_CHAIN if is_p0_1 else CODE_CHAIN,
         "triageCodeNodes": [] if is_p0_1 else sorted(TRIAGE_CODE_NODES), "triageExamples": triage_examples},
        ensure_ascii=False,
    )
    if container:
        command = ["docker", "exec", "-i", container, "node", "-e", NODE_RUNNER]
    elif shutil.which("node"):
        command = ["node", "-e", NODE_RUNNER]
    else:
        raise RuntimeError("Node.js not found; supply --node-container with an available container")
    process = subprocess.run(command, input=payload, text=True, capture_output=True, check=False)
    if process.returncode:
        raise RuntimeError(f"Node.js run failed: {process.stderr.strip()}")
    local_result = json.loads(process.stdout)
    actual_by_id = {row["id"]: row["actual"] for row in local_result["cases"]}
    failed = 0
    for case in cases:
        actual = actual_by_id[case["id"]]
        expected = case["expect"]
        response = actual["response"]
        problems = []
        if actual["status_code"] != expected["http_status"]:
            problems.append(f"HTTP {actual['status_code']} != {expected['http_status']}")
        for key in ("route", "reason", "codes", "ticket", "agents", "sources", "security"):
            if key in expected and response.get(key) != expected[key]:
                problems.append(f"{key}: {response.get(key)!r} != {expected[key]!r}")
        if "must_not_route" in expected and response.get("route") == expected["must_not_route"]:
            problems.append("unexpected blocked route")
        for phrase in expected.get("answer_contains", []):
            if phrase not in response.get("answer", ""):
                problems.append(f"answer missing {phrase!r}")
        if expected.get("llm_calls") != 0:
            problems.append("this local Mock runner only supports llm_calls=0")
        if actual["status_code"] == 200:
            required = {"request_id", "route", "answer", "sources", "ticket", "agents", "security"}
            if not required.issubset(response):
                problems.append("common response fields missing")
            if response.get("request_id") != tests[cases.index(case)]["body"]["request_id"]:
                problems.append("request_id changed")
        if problems:
            failed += 1
            print(f"FAIL {case['id']}: {'; '.join(problems)}")
        else:
            print(f"PASS {case['id']} (local Code simulation)")
    parser_by_id = {row["id"]: row["actual_error"] for row in local_result["parser"]}
    for example in triage_examples:
        actual_error = parser_by_id[example["id"]]
        expected_error = example.get("expect_error")
        if actual_error != expected_error:
            failed += 1
            print(f"FAIL parser {example['id']}: {actual_error!r} != {expected_error!r}")
        else:
            print(f"PASS parser {example['id']}")
    total = len(cases) + len(triage_examples)
    print(f"local result: {total - failed}/{total} passed; n8n webhook and triage Agent were not called")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="validate a local P0-1 or P0-2 Mock workflow")
    check.add_argument("workflow", nargs="?", default="workflows/oke-support-02.json")
    local = sub.add_parser("test-local", help="run Code nodes only; does not call n8n")
    local.add_argument("cases", nargs="?", default="cases/support-input.json")
    local.add_argument("--workflow", default="workflows/oke-support-02.json")
    local.add_argument("--node-container", help="existing container that has Node.js")
    args = parser.parse_args()
    try:
        workflow = resolve_path(args.workflow)
        flow = check_flow(workflow)
        stage = "P0-1" if len(flow["nodes"]) == len(P0_1_NODES) else "P0-2"
        print(f"LOCAL {stage} CHECK PASS (not the official evaluation-kit check)")
        if args.command == "test-local":
            return run_local(flow, resolve_path(args.cases), args.node_container)
        return 0
    except (KeyError, OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
