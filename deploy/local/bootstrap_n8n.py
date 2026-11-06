#!/usr/bin/env python3
"""Bootstrap the isolated local n8n owner, per-purpose credentials and root workflows once."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEPLOY = HERE.parent
REPO = DEPLOY.parent
PRIVATE = HERE / ".private"
URL = "http://127.0.0.1:15679"
CONTAINER = "oke-local-n8n-1"


def read_env(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines()
                if line and not line.startswith("#") and "=" in line)


def private_write(path: Path, content: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(path, 0o600)


def api(path: str, *, method="GET", body=None, cookies=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if data else {}
    if cookies:
        headers["Cookie"] = cookies
    request = urllib.request.Request(URL + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read()), response.headers.get_all("Set-Cookie", [])
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read())
        except Exception:
            payload = {}
        return error.code, payload, error.headers.get_all("Set-Cookie", [])


def owner_login(owner: dict[str, str]) -> tuple[str, str]:
    if not owner.get("N8N_OWNER_PASSWORD"):
        owner["N8N_OWNER_PASSWORD"] = secrets.token_urlsafe(48)
        owner.setdefault("N8N_OWNER_EMAIL", "n8n.local@oke.test")
        private_write(PRIVATE / "n8n-owner.env", "".join(f"{k}={v}\n" for k, v in owner.items()))
    status, result, cookies = api("/rest/login", method="POST", body={
        "emailOrLdapLoginId": owner["N8N_OWNER_EMAIL"], "password": owner["N8N_OWNER_PASSWORD"]})
    if status != 200:
        status, _, _ = api("/rest/owner/setup", method="POST", body={
            "email": owner["N8N_OWNER_EMAIL"], "firstName": "OKE", "lastName": "Local Admin",
            "password": owner["N8N_OWNER_PASSWORD"]})
        if status != 200:
            raise SystemExit("local n8n owner setup/login failed; no credentials were printed")
        status, result, cookies = api("/rest/login", method="POST", body={
            "emailOrLdapLoginId": owner["N8N_OWNER_EMAIL"], "password": owner["N8N_OWNER_PASSWORD"]})
    if status != 200 or not result.get("data", {}).get("id"):
        raise SystemExit("local n8n owner login failed")
    cookie = "; ".join(c.split(";", 1)[0] for c in cookies if c)
    return result["data"]["id"], cookie


def import_credentials(user_id: str, cookie: str, backend: dict, search: dict, index: dict,
                       openai: dict) -> list[dict]:
    _, response, _ = api("/rest/credentials", cookies=cookie)
    existing = response.get("data", []) if isinstance(response, dict) else []
    by_name = {(c.get("name"), c.get("type")): c for c in existing}
    entries = [
        ("OKE Team Webhook", "httpHeaderAuth", {"name": "X-Team-Key", "value": backend["N8N_WEBHOOK_KEY"]}),
        ("OKE RAG Search", "httpHeaderAuth", {"name": "X-Team-Key", "value": search["SEARCH_TEAM_KEY"]}),
        ("OKE RAG Index", "httpHeaderAuth", {"name": "X-Team-Key", "value": index["INDEX_TEAM_KEY"]}),
        ("OKE Backend Internal", "httpHeaderAuth", {"name": "X-Api-Key", "value": backend["INTERNAL_API_KEY"]}),
    ]
    if openai.get("OPENAI_API_KEY"):
        entries.append(("OpenAI account", "openAiApi", {"apiKey": openai["OPENAI_API_KEY"]}))
    new = []
    for name, kind, data in entries:
        prior = by_name.get((name, kind))
        if prior:
            new.append({"id": prior["id"], "name": name, "type": kind})
        else:
            new.append({"id": str(uuid.uuid4()), "name": name, "type": kind, "data": data})
    missing = [item for item in new if (item["name"], item["type"]) not in by_name]
    if missing:
        source = PRIVATE / "credentials-import.json"
        private_write(source, json.dumps(missing))
        try:
            subprocess.run(["docker", "cp", str(source), f"{CONTAINER}:/tmp/local-credentials.json"],
                           check=True, capture_output=True)
            subprocess.run(["docker", "exec", "-u", "0:0", CONTAINER, "chown", "node:node",
                            "/tmp/local-credentials.json"], check=True, capture_output=True)
            subprocess.run(["docker", "exec", "-u", "0:0", CONTAINER, "chmod", "600",
                            "/tmp/local-credentials.json"], check=True, capture_output=True)
            result = subprocess.run(["docker", "exec", CONTAINER, "n8n", "import:credentials",
                                    "--input=/tmp/local-credentials.json", f"--userId={user_id}"],
                                   capture_output=True)
            if result.returncode:
                raise SystemExit("local n8n credential import failed; CLI output withheld")
        finally:
            subprocess.run(["docker", "exec", "-u", "0:0", CONTAINER, "rm", "-f",
                            "/tmp/local-credentials.json"], capture_output=True)
            source.unlink(missing_ok=True)
    _, response, _ = api("/rest/credentials", cookies=cookie)
    metadata = response.get("data", [])
    safe = [{"id": c["id"], "name": c["name"], "type": c["type"]} for c in metadata]
    private_write(PRIVATE / "credential-metadata.json", json.dumps(safe, indent=2) + "\n")
    return safe


def main() -> None:
    owner = read_env(PRIVATE / "n8n-owner.env") if (PRIVATE / "n8n-owner.env").exists() else {}
    user_id, cookie = owner_login(owner)
    backend, search, index = (read_env(PRIVATE / name) for name in
                              ("backend.env", "search.env", "index.env"))
    openai = read_env(PRIVATE / "openai.env") if (PRIVATE / "openai.env").exists() else {}
    creds = import_credentials(user_id, cookie, backend, search, index, openai)
    selected = ["oke-search", "oke-index", "oke-handoff", "oke-errors"]
    if any(c["type"] == "openAiApi" for c in creds):
        selected.insert(0, "oke-support")
    output = PRIVATE / "workflows"
    command = ["python3", str(DEPLOY / "prepare_n8n_workflows.py"), "--source", str(REPO / "workflows"),
               "--credentials", str(PRIVATE / "credential-metadata.json"), "--output", str(output),
               "--only", *selected]
    subprocess.run(command, cwd=REPO, check=True, capture_output=True, text=True)
    status, response, _ = api("/rest/workflows", cookies=cookie)
    if status != 200:
        raise SystemExit("could not inspect local n8n workflow state")
    rows = response.get("data", [])
    existing = {w.get("id"): w for w in rows if isinstance(w, dict)}
    plan = (output / "plan.txt").read_text().splitlines()
    missing = [line.split()[0] for line in plan if line.split()[1] not in existing]
    if missing:
        import_dir = PRIVATE / "workflow-import"
        import_dir.mkdir(mode=0o700, exist_ok=True)
        for stem in missing:
            (import_dir / f"{stem}.json").write_bytes((output / f"{stem}.json").read_bytes())
        subprocess.run(["docker", "cp", str(import_dir), f"{CONTAINER}:/tmp/local-workflows"],
                       check=True, capture_output=True)
        result = subprocess.run(["docker", "exec", CONTAINER, "n8n", "import:workflow", "--separate",
                                 "--input=/tmp/local-workflows", f"--userId={user_id}"], capture_output=True)
        subprocess.run(["docker", "exec", "-u", "0:0", CONTAINER, "rm", "-rf", "/tmp/local-workflows"],
                       capture_output=True)
        for f in import_dir.iterdir():
            f.unlink()
        import_dir.rmdir()
        if result.returncode:
            raise SystemExit("local n8n workflow import failed; CLI output withheld")
    published = []
    for line in plan:
        stem, workflow_id, action = line.split()
        if action == "publish" and not existing.get(workflow_id, {}).get("active"):
            result = subprocess.run(["docker", "exec", CONTAINER, "n8n", "publish:workflow",
                                     f"--id={workflow_id}"], capture_output=True)
            if result.returncode:
                raise SystemExit(f"local workflow publish failed: {stem}")
            published.append(stem)
    print(f"Local workflows prepared: {len(selected)} selected; published {len(published)} newly activated trigger workflows.")
    print("Credential values and owner password were withheld; local n8n owner handoff is in mode-0600 private settings.")


if __name__ == "__main__":
    main()
