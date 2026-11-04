#!/usr/bin/env python3
"""Local P0-1 checker for oke-support; not the team's evaluation-kit flow.py.

This tool checks the current six-node skeleton and runs Code-node snippets with
Node.js. It does not import, publish, or call an n8n workflow.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAIN = [
    "N01 Support webhook",
    "N02 Normalize input",
    "N03 Validate employee MOCK",
    "N04 Injection rules",
    "N22 Finalize P0-1",
    "N23 Respond",
]
CODE_CHAIN = CHAIN[1:-1]
NODE_RUNNER = r"""
const fs = require('fs');
const vm = require('vm');
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
const nodes = Object.fromEntries(data.flow.nodes.map(node => [node.name, node]));
const result = [];
for (const test of data.tests) {
  let value = {body: test.body};
  for (const name of data.codeChain) {
    const code = nodes[name].parameters.jsCode;
    const items = vm.runInNewContext('(function(){' + code + '})()', {
      $input: {first: () => ({json: value})}
    }, {timeout: 1000});
    if (!Array.isArray(items) || items.length !== 1 || !items[0].json) {
      throw new Error(test.id + ': invalid output from ' + name);
    }
    value = items[0].json;
  }
  result.push({id: test.id, actual: value});
}
process.stdout.write(JSON.stringify(result));
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
    if set(by_name) != set(CHAIN):
        raise ValueError("P0-1 node set differs from the six-node skeleton")
    if flow.get("name") != "oke-support":
        raise ValueError("workflow name must be oke-support")
    if flow.get("settings", {}).get("executionOrder") != "v1":
        raise ValueError("executionOrder must be v1")

    webhook = by_name[CHAIN[0]]
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
    if any("langchain" in node["type"] or node["type"] == "n8n-nodes-base.httpRequest" for node in nodes):
        raise ValueError("P0-1 skeleton must have no LLM or HTTP request nodes")
    for source, target in zip(CHAIN, CHAIN[1:]):
        edges = flow.get("connections", {}).get(source, {}).get("main")
        if edges != [[{"node": target, "type": "main", "index": 0}]]:
            raise ValueError(f"expected single connection {source} -> {target}")
    if CHAIN[-1] in flow.get("connections", {}):
        raise ValueError("Respond must be the terminal node")
    for name in CODE_CHAIN:
        if by_name[name]["type"] != "n8n-nodes-base.code":
            raise ValueError(f"{name} must be a Code node")

    fixture = load_json(ROOT / "fixtures/employees.json")
    employees = fixture["items"]
    if len(employees) != 6 or any(set(row) != {"name", "dept"} for row in employees):
        raise ValueError("employee fixture must contain six name/dept rows")
    mock_code = by_name["N03 Validate employee MOCK"]["parameters"]["jsCode"]
    for row in employees:
        if f"name: '{row['name']}', dept: '{row['dept']}'" not in mock_code:
            raise ValueError(f"workflow Mock differs from fixture: {row['name']}")
    return flow


def run_local(flow, case_path: Path, container: str | None):
    cases = load_json(case_path)["cases"]
    tests = []
    for case in cases:
        request_file = ROOT / case["request_file"]
        tests.append({"id": case["id"], "body": load_json(request_file)})
    payload = json.dumps({"flow": flow, "tests": tests, "codeChain": CODE_CHAIN}, ensure_ascii=False)
    if container:
        command = ["docker", "exec", "-i", container, "node", "-e", NODE_RUNNER]
    elif shutil.which("node"):
        command = ["node", "-e", NODE_RUNNER]
    else:
        raise RuntimeError("Node.js not found; supply --node-container with an available container")
    process = subprocess.run(command, input=payload, text=True, capture_output=True, check=False)
    if process.returncode:
        raise RuntimeError(f"Node.js run failed: {process.stderr.strip()}")
    actual_by_id = {row["id"]: row["actual"] for row in json.loads(process.stdout)}
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
        if expected.get("llm_calls") != 0:
            problems.append("this local P0-1 runner only supports llm_calls=0")
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
    print(f"local result: {len(cases) - failed}/{len(cases)} passed; n8n webhook was not called")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="validate the local P0-1 JSON skeleton")
    check.add_argument("workflow", nargs="?", default="workflows/oke-support.json")
    local = sub.add_parser("test-local", help="run Code nodes only; does not call n8n")
    local.add_argument("cases", nargs="?", default="cases/support-input.json")
    local.add_argument("--workflow", default="workflows/oke-support.json")
    local.add_argument("--node-container", help="existing container that has Node.js")
    args = parser.parse_args()
    try:
        workflow = resolve_path(args.workflow)
        flow = check_flow(workflow)
        print("LOCAL P0-1 CHECK PASS (not the official evaluation-kit check)")
        if args.command == "test-local":
            return run_local(flow, resolve_path(args.cases), args.node_container)
        return 0
    except (KeyError, OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
