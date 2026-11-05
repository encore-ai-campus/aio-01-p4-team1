"""Explicit employee seed and first-admin commands; no startup side effects."""

import argparse
import json
import os

import httpx
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.clients.data_api import SourceError, fetch_employees
from app.core.config import Settings
from app.db.session import create_db_engine, create_session_factory
from app.services.bootstrap import BootstrapError, bootstrap_admin, seed_employees


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
            # Live contract must be explicitly confirmed by the operator first.
            header = os.environ.get("DATA_API_EMPLOYEES_AUTH_HEADER")
            if not settings.data_api_url or not settings.data_api_key or not header:
                raise BootstrapError("employee_source_configuration_required")
            with httpx.Client(base_url=str(settings.data_api_url).rstrip("/") + "/",
                              headers={header: settings.data_api_key.get_secret_value()},
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
