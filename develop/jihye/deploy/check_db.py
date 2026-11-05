"""Run checks on the private Compose network and redact subprocess output."""

import argparse
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="include all backend regression tests")
    args = parser.parse_args()
    values = dotenv_values(ROOT / "deploy/.env")
    if not values.get("DATABASE_URL") or not values.get("POSTGRES_PASSWORD"):
        print("Private deploy/.env is missing DB settings")
        return 1
    command = ["docker", "compose", "--env-file", "deploy/.env", "-f", "deploy/compose.yaml",
               "-f", "deploy/compose.check.yaml", "run", "--rm", "db-check"]
    if args.all:
        command += ["python", "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"]
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
