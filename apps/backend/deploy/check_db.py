"""Run checks on the private Compose network and redact subprocess output."""

import argparse
import subprocess
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="include all backend regression tests")
    group.add_argument("--migrations", action="store_true", help="check the installed business schema")
    group.add_argument("--alembic", choices=("history", "heads", "current", "upgrade"),
                       help="run a read command or upgrade head inside this Compose network")
    args = parser.parse_args()
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
        print("Private DB settings must match this Compose postgres service")
        return 1
    command = ["docker", "compose", "--env-file", "deploy/.env", "-f", "deploy/compose.yaml",
               "-f", "deploy/compose.check.yaml", "run", "--rm", "db-check"]
    if args.all:
        command += ["python", "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"]
    elif args.migrations:
        command += ["python", "-m", "pytest", "tests/integration/test_migrations.py", "-q",
                    "--tb=short", "-p", "no:cacheprovider"]
    elif args.alembic:
        command += ["python", "-m", "alembic", "-c", "migrations/alembic.ini", args.alembic]
        if args.alembic == "upgrade":
            command += ["head"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    output = result.stdout + result.stderr
    for name in ("POSTGRES_PASSWORD", "DATABASE_URL"):
        value = values.get(name)
        if value:
            output = output.replace(value, "[REDACTED]")
    print(output, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
