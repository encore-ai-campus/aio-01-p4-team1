"""Provision a dedicated LOGIN for the local validation DB, never a VM."""

import os
from pathlib import Path
import secrets
import subprocess

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent


def main():
    path = ROOT / "deploy/.env.backend"
    if path.exists():
        print("Private backend settings already exist; unchanged")
        return 0
    values = dotenv_values(ROOT / "deploy/.env")
    try:
        url = make_url(values["DATABASE_URL"])
        if (url.host != "postgres" or url.username != values["POSTGRES_USER"]
                or url.database != values["POSTGRES_DB"] or url.password != values["POSTGRES_PASSWORD"]):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        print("Matching private local DB settings are required")
        return 1
    password = secrets.token_urlsafe(36)
    # Generated URL-safe password and fixed identifiers; no user SQL interpolation.
    sql = f"BEGIN; CREATE ROLE oke_backend_login LOGIN PASSWORD '{password}'; GRANT oke_app TO oke_backend_login; COMMIT;"
    command = ["docker", "compose", "--env-file", "deploy/.env", "-f", "deploy/compose.yaml",
               "exec", "-T", "postgres", "sh", "-c",
               'PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1']
    result = subprocess.run(command, input=sql, text=True, capture_output=True, cwd=ROOT)
    if result.returncode:
        print("Local runtime role setup failed; settings not written")
        return 1
    runtime_url = url.set(username="oke_backend_login", password=password)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as file:
        file.write("DATABASE_URL=" + runtime_url.render_as_string(hide_password=False) + "\nSERVICE_MODE=app\n")
    print("Private local runtime settings created; values omitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
