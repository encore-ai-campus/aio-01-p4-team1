#!/usr/bin/env python3
"""Create private, Mac-only runtime settings for the isolated oke-local stack."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import secrets
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEPLOY = HERE.parent
REPO = DEPLOY.parent
MANIFEST = REPO / "rag/rag-permissions.json"
DOCS = REPO / "knowledge"


def write_private(path: Path, content: str, *, preserve: bool = True) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    if path.exists() and preserve:
        os.chmod(path, 0o600)
        return
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(content)
    os.chmod(path, 0o600)


def env(**values: str) -> str:
    return "".join(f"{name}={value}\n" for name, value in values.items())


def verify_source() -> list[dict]:
    if not (REPO / "data-api/server.py").is_file() or not DOCS.is_dir():
        raise SystemExit("repository must contain data-api/server.py and knowledge/")
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    docs = entries.get("documents", entries) if isinstance(entries, dict) else entries
    if isinstance(docs, dict):
        docs = [{"path": f"{name}.md", **metadata} for name, metadata in docs.items()]
    if not isinstance(docs, list):
        raise SystemExit("rag permissions manifest format is not a document mapping/list")
    checked = []
    for item in docs:
        rel = item.get("path") or item.get("file")
        expected = item.get("sha256") or item.get("hash")
        if not isinstance(rel, str) or not isinstance(expected, str):
            raise SystemExit("rag permissions manifest lacks path/sha256")
        candidate = DOCS / rel
        if not candidate.is_file():
            raise SystemExit(f"source document missing: {rel}")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if not secrets.compare_digest(digest, expected.lower()):
            raise SystemExit(f"source document hash mismatch: {rel}")
        checked.append({"path": rel, "sha256": digest})
    return checked


def read_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            values[name] = value
    return values


def compose(*args: str) -> list[str]:
    return ["docker", "compose", "--env-file", "local/.private/compose.env",
            "-f", "compose.vm.yaml", "-f", "compose.local.yaml", "-p", "oke-local", *args]


def provision_roles(_: argparse.Namespace) -> None:
    p = HERE / ".private"
    bootstrap = read_env(p / "compose.env")
    backend = read_env(p / "backend.env")
    search = read_env(p / "search.env")
    index = read_env(p / "index.env")
    import re
    roles = [
        ("oke_app_local", "oke_app", backend["DATABASE_URL"]),
        ("oke_rag_search_local", "oke_rag_search", search["DATABASE_URL"]),
        ("oke_rag_index_local", "oke_rag_index", index["DATABASE_URL"]),
    ]
    sql = []
    for login, group, url in roles:
        match = re.fullmatch(r"postgresql(?:\+psycopg)?://([^:]+):([^@]+)@postgres:5432/([^?]+)", url)
        if not match:
            raise SystemExit("local database URL format invalid")
        name, password = match.group(1), match.group(2)
        if name != login or not re.fullmatch(r"[A-Za-z0-9_]+", name):
            raise SystemExit("local database role identity invalid")
        sql.append(
            f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{name}') "
            f"THEN CREATE ROLE {name} LOGIN INHERIT PASSWORD '{password}'; "
            f"ELSE ALTER ROLE {name} WITH LOGIN INHERIT PASSWORD '{password}'; END IF; END $$;"
            f" GRANT {group} TO {name};"
        )
    sql_file = p / "role-provision.sql"
    write_private(sql_file, "\n".join(sql) + "\n", preserve=False)
    container = "oke-local-postgres-1"
    try:
        subprocess.run(["docker", "cp", str(sql_file), f"{container}:/tmp/role-provision.sql"],
                       check=True, capture_output=True)
        run = subprocess.run(["docker", "exec", container, "sh", "-c",
                              'PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/role-provision.sql'],
                             text=True, capture_output=True)
        subprocess.run(["docker", "exec", container, "rm", "-f", "/tmp/role-provision.sql"],
                       check=False, capture_output=True)
        if run.returncode:
            raise SystemExit("database role provisioning failed (PostgreSQL rejected role configuration)")
    finally:
        sql_file.unlink(missing_ok=True)
    print("Created/verified three least-privilege LOGINs with their existing NOLOGIN group grants.")


def import_openai_clipping(args: argparse.Namespace) -> None:
    raw = plistlib.loads(args.path.expanduser().read_bytes())
    try:
        value = raw["UTI-Data"]["public.utf8-plain-text"]
    except (KeyError, TypeError):
        raise SystemExit("textClipping does not contain public UTF-8 plain text") from None
    if not isinstance(value, str):
        raise SystemExit("textClipping plain text is not a string")
    match = re.fullmatch(r"[\s\"']*(sk-[A-Za-z0-9_-]{30,})[\s\"']*", value)
    if not match:
        raise SystemExit("textClipping did not contain exactly one OpenAI API key")
    secret = match.group(1)
    target = HERE / ".private/openai.env"
    if target.exists():
        current = read_env(target).get("OPENAI_API_KEY")
        if current != secret:
            raise SystemExit("a different local OpenAI key is already configured; refusing to overwrite")
        os.chmod(target, 0o600)
    else:
        write_private(target, f"OPENAI_API_KEY={secret}\n", preserve=False)
    print("OpenAI key validated and stored in local-only mode-0600 settings; value withheld.")


def repair_rag_dsn(_: argparse.Namespace) -> None:
    private = HERE / ".private"
    index_path, search_path = private / "index.env", private / "search.env"
    index, search = read_env(index_path), read_env(search_path)
    import re
    pattern = re.compile(r"^postgresql(?:\+psycopg)?://([^:]+):([^@]+)@postgres:5432/([^?]+)$")
    match = pattern.fullmatch(index.get("DATABASE_URL", ""))
    if not match or match.group(1) != "oke_rag_index_local":
        raise SystemExit("local index database settings are not in the expected format")
    name, _, db_name = match.groups()
    rotated = secrets.token_urlsafe(48)
    sql = private / "rotate-index-password.sql"
    write_private(sql, f"ALTER ROLE {name} WITH PASSWORD '{rotated}';\n", preserve=False)
    container = "oke-local-postgres-1"
    try:
        subprocess.run(["docker", "cp", str(sql), f"{container}:/tmp/rotate-index-password.sql"],
                       check=True, capture_output=True)
        result = subprocess.run(["docker", "exec", container, "sh", "-c",
                                 'PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/rotate-index-password.sql'],
                                capture_output=True)
        subprocess.run(["docker", "exec", "-u", "0:0", container, "rm", "-f", "/tmp/rotate-index-password.sql"],
                       capture_output=True)
        if result.returncode:
            raise SystemExit("local index database password rotation failed")
    finally:
        sql.unlink(missing_ok=True)
    search_match = pattern.fullmatch(search.get("DATABASE_URL", ""))
    if not search_match or search_match.group(1) != "oke_rag_search_local":
        raise SystemExit("local search database settings are not in the expected format")
    index["DATABASE_URL"] = f"postgresql://{name}:{rotated}@postgres:5432/{db_name}"
    search["DATABASE_URL"] = f"postgresql://{search_match.group(1)}:{search_match.group(2)}@postgres:5432/{search_match.group(3)}"
    write_private(index_path, env(**index), preserve=False)
    write_private(search_path, env(**search), preserve=False)
    print("Local RAG DSNs repaired; affected index LOGIN password rotated. Values withheld.")


def init(args: argparse.Namespace) -> None:
    verified = verify_source()
    private = HERE / ".private"
    key = lambda: secrets.token_urlsafe(48)
    db_name, db_boot, app_login, search_login, index_login = (
        "oke_local", "oke_local_bootstrap", "oke_app_local", "oke_rag_search_local", "oke_rag_index_local"
    )
    boot_password, app_password, search_password, index_password = key(), key(), key(), key()
    internal_key, team_key, search_key, index_key, session_key = key(), key(), key(), key(), key()
    n8n_encryption, runner_token = secrets.token_hex(32), key()
    sandbox_api_key, sandbox_registration, sandbox_runner_key = key(), key(), key()
    values = {
        "compose.env": env(
            N8N_VERSION="2.42.6", N8N_SANDBOX_VERSION="1.8.1",
            POSTGRES_DB=db_name, POSTGRES_USER=db_boot, POSTGRES_PASSWORD=boot_password,
            SANDBOX_API_KEYS=sandbox_api_key,
            SANDBOX_API_RUNNER_REGISTRATION_TOKEN=sandbox_registration,
            SANDBOX_API_RUNNER_API_KEY=sandbox_runner_key,
            SANDBOX_RUNNER_REGISTRATION_TOKEN=sandbox_registration,
            SANDBOX_RUNNER_API_KEYS=sandbox_runner_key,
        ),
        "n8n.env": env(
            N8N_ENCRYPTION_KEY=n8n_encryption, N8N_RUNNERS_AUTH_TOKEN=runner_token,
            N8N_BLOCK_ENV_ACCESS_IN_NODE="false", N8N_PROXY_HOPS="1",
            DB_TYPE="sqlite", SERVICE_MODE="app", N8N_SANDBOX_SERVICE_URL="http://sandbox-api:8080",
            N8N_SANDBOX_SERVICE_API_KEY=sandbox_api_key,
        ),
        "backend.env": env(
            DATABASE_URL=f"postgresql+psycopg://{app_login}:{app_password}@postgres:5432/{db_name}",
            SERVICE_MODE="app", INTERNAL_API_KEY=internal_key, SESSION_SECRET=session_key,
            N8N_WEBHOOK_URL="http://n8n:5678/webhook/oke-support",
            N8N_WEBHOOK_KEY=team_key, DATA_API_URL="http://data-api:8800",
            DATA_API_EMPLOYEES_NO_AUTH="true", BACKEND_ORIGIN="http://localhost:3001",
        ),
        "migrate.env": env(
            DATABASE_URL=f"postgresql+psycopg://{db_boot}:{boot_password}@postgres:5432/{db_name}",
        ),
        "search.env": env(
            DATABASE_URL=f"postgresql+psycopg://{search_login}:{search_password}@postgres:5432/{db_name}",
            SEARCH_TEAM_KEY=search_key, SEARCH_MODE="live", SEARCH_HOST="0.0.0.0", SEARCH_PORT="8765",
        ),
        "index.env": env(
            DATABASE_URL=f"postgresql+psycopg://{index_login}:{index_password}@postgres:5432/{db_name}",
            INDEX_TEAM_KEY=index_key, INDEX_MODE="live", INDEX_HOST="0.0.0.0", INDEX_PORT="8766",
        ),
        "admin-handoff.env": env(BOOTSTRAP_ADMIN_PASSWORD=key()),
        "n8n-owner.env": env(N8N_OWNER_EMAIL="n8n.local@oke.test", N8N_OWNER_PASSWORD=key()),
    }
    private.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(private, 0o700)
    for name, content in values.items():
        path = private / name
        additions = read_env(path) if path.exists() else {}
        for line in content.splitlines():
            k, v = line.split("=", 1)
            additions.setdefault(k, v)
        write_private(path, env(**additions), preserve=False)
    write_private(private / "source-manifest.json", json.dumps(verified, indent=2) + "\n")
    print(f"Initialized isolated local settings; verified {len(verified)} source documents.")
    print(f"Admin handoff file: {private / 'admin-handoff.env'} (mode 0600; do not print or commit)")
    if (private / "openai.env").exists():
        os.chmod(private / "openai.env", 0o600)
        print("An approved local OpenAI key is configured in mode-0600 settings; value withheld.")
    else:
        print("No OpenAI key was generated. Add an approved local key only through import-openai-clipping.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("init", help="create private local settings; existing settings are preserved")
    setup.set_defaults(func=init)
    roles = sub.add_parser("provision-db-roles", help="provision separate app/search/index LOGINs")
    roles.set_defaults(func=provision_roles)
    openai = sub.add_parser("import-openai-clipping", help="extract a single key from a macOS textClipping file without printing it")
    openai.add_argument("path", type=Path)
    openai.set_defaults(func=import_openai_clipping)
    repair = sub.add_parser("repair-rag-dsn", help="repair local libpq DSNs and rotate the index LOGIN secret")
    repair.set_defaults(func=repair_rag_dsn)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
