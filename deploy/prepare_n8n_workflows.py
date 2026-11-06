#!/usr/bin/env python3
"""Prepare root workflows using explicit per-node VM credential mappings."""

import argparse
import json
from pathlib import Path

IDS = {
    "oke-support": "okeSupportFlow01",
    "oke-search": "okeSearchFlow01",
    "oke-index": "okeIndexFlow01",
    "oke-handoff": "okeHandoffFlow01",
    "oke-errors": "okeErrorsFlow01",
}

TEAM = "OKE Team Webhook"
SEARCH = "OKE RAG Search"
INDEX = "OKE RAG Index"
BACKEND = "OKE Backend Internal"

NODE_CREDENTIALS = {
    "oke-support": {
        "N01 Support webhook": ("httpHeaderAuth", TEAM),
        "N09 C03 HTTP": ("httpHeaderAuth", TEAM),
        "N20 C04 HTTP": ("httpHeaderAuth", TEAM),
        "N06 Triage model": ("openAiApi", None),
        "N13 Writer model": ("openAiApi", None),
        "N14 Verifier model": ("openAiApi", None),
    },
    "oke-search": {
        "검색 요청 수신": ("httpHeaderAuth", TEAM),
        "실제 검색 서비스 호출": ("httpHeaderAuth", SEARCH),
    },
    "oke-index": {"실제 색인 서비스 호출": ("httpHeaderAuth", INDEX)},
    "oke-handoff": {
        "H01 Handoff Webhook": ("httpHeaderAuth", TEAM),
        "H04 Create Ticket App": ("httpHeaderAuth", BACKEND),
        "H04 Retry Ticket App": ("httpHeaderAuth", BACKEND),
        "H08 Store Alert App": ("httpHeaderAuth", BACKEND),
        "H09 Store DLQ App": ("httpHeaderAuth", BACKEND),
    },
    "oke-errors": {
        "E03 Store Alert App": ("httpHeaderAuth", BACKEND),
        "E04 Store DLQ App": ("httpHeaderAuth", BACKEND),
    },
}


def prepare(source_dir: Path, credential_meta: Path, output_dir: Path, only=None):
    credentials = json.loads(credential_meta.read_text(encoding="utf-8"))
    if not isinstance(credentials, list):
        raise ValueError("credential_metadata_invalid")
    named = {}
    openai = []
    for item in credentials:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) for k in ("id", "name", "type")):
            raise ValueError("credential_metadata_invalid")
        if item["type"] == "httpHeaderAuth":
            named[item["name"]] = item
        elif item["type"] == "openAiApi":
            openai.append(item)
    selected = list(IDS) if not only else list(only)
    if not selected or set(selected) - IDS.keys():
        raise ValueError("workflow_selection_invalid")
    required = {name for stem in selected for _, name in NODE_CREDENTIALS[stem].values()
                if name is not None}
    needs_openai = any(name is None for stem in selected
                       for _, name in NODE_CREDENTIALS[stem].values())
    if required - named.keys() or (needs_openai and len(openai) != 1):
        raise ValueError("credential_mapping_incomplete")

    output_dir.mkdir(parents=True, exist_ok=True)
    plan = []
    for stem in selected:
        workflow = json.loads((source_dir / f"{stem}.json").read_text(encoding="utf-8"))
        workflow["id"] = IDS[stem]
        workflow["active"] = False
        seen = set()
        for node in workflow.get("nodes", []):
            name = node.get("name")
            if name in NODE_CREDENTIALS[stem]:
                cred_type, cred_name = NODE_CREDENTIALS[stem][name]
                metadata = openai[0] if cred_name is None else named[cred_name]
                if cred_type not in (node.get("credentials") or {}):
                    raise ValueError("workflow_credential_type_mismatch")
                node["credentials"][cred_type] = {"id": metadata["id"], "name": metadata["name"]}
                seen.add(name)
            if node.get("credentials"):
                for ref in node["credentials"].values():
                    if "REPLACE_WITH" in str(ref.get("id", "")):
                        raise ValueError("workflow_credential_placeholder")
        missing = set(NODE_CREDENTIALS[stem]) - seen
        if missing:
            raise ValueError("workflow_node_mapping_missing")
        (output_dir / f"{stem}.json").write_text(
            json.dumps(workflow, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        types = {node.get("type", "") for node in workflow.get("nodes", [])}
        publish = any(t.endswith((".webhook", ".errorTrigger", ".scheduleTrigger")) for t in types)
        plan.append(f"{stem} {workflow['id']} {'publish' if publish else 'skip'}")
    (output_dir / "plan.txt").write_text("\n".join(plan) + "\n", encoding="utf-8")
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("workflows"))
    parser.add_argument("--credentials", type=Path, required=True,
                        help="Sanitized metadata only: id/name/type; never credential data")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", nargs="+", choices=tuple(IDS),
                        help="Limit local preparation to workflows whose required credentials are present")
    args = parser.parse_args()
    try:
        plan = prepare(args.source, args.credentials, args.output, only=args.only)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(2, f"Workflow preparation failed: {error}\n")
    for item in plan:
        print(item)


if __name__ == "__main__":
    main()
