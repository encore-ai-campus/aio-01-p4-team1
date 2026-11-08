"""Verify app and RAG fixture persistence across a restart of the private Compose stack."""

import argparse
import subprocess
import uuid
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent
BASE = ["docker", "compose", "--env-file", "deploy/.env", "-f", "deploy/compose.yaml"]
CHECK = [*BASE, "-f", "deploy/compose.check.yaml"]


def _run(command: list[str], *, run_id: str | None = None,
         phase: str | None = None, values: dict[str, str | None]) -> int:
    if run_id and phase:
        command = [*command[:command.index("db-check")], "-e", f"P1_4_RUN_ID={run_id}",
                   "-e", f"P1_4_PHASE={phase}", *command[command.index("db-check"):]]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    output = result.stdout + result.stderr
    for name in ("POSTGRES_PASSWORD", "DATABASE_URL"):
        secret = values.get(name)
        if secret:
            output = output.replace(secret, "[REDACTED]")
    print(output, end="")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-private-db", action="store_true",
                        help="confirm this operates only on deploy/compose.yaml's private DB")
    args = parser.parse_args()
    if not args.confirm_private_db:
        parser.error("pass --confirm-private-db only for the isolated local Compose DB")
    values = dotenv_values(ROOT / "deploy/.env")
    if not values.get("DATABASE_URL") or not values.get("POSTGRES_PASSWORD"):
        print("Private deploy/.env is missing DB settings")
        return 1
    try:
        url = make_url(values["DATABASE_URL"])
        if (url.host != "postgres" or url.database != values.get("POSTGRES_DB")
                or url.username != values.get("POSTGRES_USER")
                or url.password != values["POSTGRES_PASSWORD"]):
            raise ValueError
    except Exception:
        print("Persistence check is restricted to the matching private Compose DB")
        return 1

    run_id = uuid.uuid4().hex[:20]
    test = [*CHECK, "run", "--rm", "db-check", "python", "-m", "pytest",
            "tests/integration/test_persistence.py", "-q", "--tb=short", "-p",
            "no:cacheprovider"]
    seeded = False
    try:
        if _run(test, run_id=run_id, phase="seed", values=values):
            return 1
        seeded = True
        print("Restarting the private PostgreSQL and backend services...")
        if _run([*BASE, "restart", "postgres", "backend"], values=values):
            return 1
        if _run([*BASE, "up", "-d", "--wait", "postgres", "backend"], values=values):
            return 1
        return _run(test, run_id=run_id, phase="verify", values=values)
    finally:
        if seeded:
            _run([*BASE, "up", "-d", "--wait", "postgres", "backend"], values=values)
            cleanup = _run(test, run_id=run_id, phase="cleanup", values=values)
            if cleanup:
                print("Fixture cleanup failed; inspect only the unique p1-4 run marker.")


if __name__ == "__main__":
    raise SystemExit(main())
