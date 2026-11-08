"""Explicit employee seed and first-admin commands; no startup side effects."""

import argparse
import json
import os
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.clients.data_api import SourceError, fetch_employees
from app.core.config import Settings
from app.db.session import create_db_engine, create_session_factory
from app.services.bootstrap import BootstrapError, bootstrap_admin, seed_employees


def employee_source_headers(data_api_url, data_api_key, auth_header, no_auth):
    """Return only an explicit auth header or verified internal no-auth mode."""
    if no_auth == "true":
        parsed = urlsplit(str(data_api_url or ""))
        if (parsed.scheme != "http" or parsed.netloc != "data-api:8800"
                or parsed.path not in ("", "/") or parsed.username or parsed.password
                or parsed.query or parsed.fragment or data_api_key or auth_header):
            raise BootstrapError("employee_source_configuration_required")
        return {}
    if not data_api_url or not data_api_key or not auth_header:
        raise BootstrapError("employee_source_configuration_required")
    if "\r" in auth_header or "\n" in auth_header:
        raise BootstrapError("employee_source_configuration_required")
    return {auth_header: data_api_key}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("seed-employees")
    admin = commands.add_parser("bootstrap-admin")
    admin.add_argument("--employee-name", required=True)
    admin.add_argument("--login-id", required=True)
    args = parser.parse_args(argv)
    engine = None
    try:
        settings = Settings()
        if args.command == "seed-employees":
            header = os.environ.get("DATA_API_EMPLOYEES_AUTH_HEADER")
            key = settings.data_api_key.get_secret_value() if settings.data_api_key else None
            headers = employee_source_headers(
                settings.data_api_url, key, header,
                os.environ.get("DATA_API_EMPLOYEES_NO_AUTH"),
            )
            with httpx.Client(base_url=str(settings.data_api_url).rstrip("/") + "/",
                              headers=headers,
                              timeout=10, follow_redirects=False, trust_env=False) as client:
                employees = fetch_employees(client)
        else:
            if not settings.bootstrap_admin_password or not settings.session_secret or not settings.session_secret.get_secret_value():
                raise BootstrapError("bootstrap_secrets_required")
        engine = create_db_engine(settings)
        with create_session_factory(engine).begin() as session:
            if args.command == "seed-employees":
                created = seed_employees(session, employees)
            else:
                created = bootstrap_admin(session, employee_name=args.employee_name, login_id=args.login_id,
                    password=settings.bootstrap_admin_password.get_secret_value())
        print(json.dumps({"ok": True, "created": created}))
        return 0
    except (SourceError, BootstrapError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    except (SQLAlchemyError, ValidationError, ValueError, httpx.HTTPError):
        print(json.dumps({"ok": False, "error": "bootstrap_failed"}))
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
