import secrets

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import Settings
from app.db.base import Base, include_migration_name
from app.db.session import DatabaseConfigurationError, create_db_engine, database_url


@pytest.mark.parametrize("value", [None, "", "not-a-url", "sqlite:///:memory:",
                                   "postgresql://user:pass@postgres/db"])
def test_database_settings_reject_invalid_or_implicit_driver(value):
    with pytest.raises(DatabaseConfigurationError):
        database_url(value)


def test_configuration_error_and_engine_do_not_reveal_password():
    private_input = secrets.token_urlsafe(24)
    with pytest.raises(DatabaseConfigurationError) as caught:
        database_url("invalid:" + private_input)
    assert private_input not in str(caught.value)
    engine = create_db_engine(Settings(database_url=f"postgresql+psycopg://fixture:{private_input}@postgres/db"))
    assert private_input not in repr(engine)
    assert not engine.echo
    assert engine.hide_parameters
    engine.dispose()


def test_only_app_and_rag_are_autogenerate_targets():
    for schema in ("app", "rag"):
        assert include_migration_name(schema, "schema", {})
        assert include_migration_name("fixture", "table", {"schema_name": schema})
    for schema in (None, "public", "other_service"):
        assert not include_migration_name(schema, "schema", {})
        assert not include_migration_name("fixture", "table", {"schema_name": schema})


def test_p0_4_has_business_models_and_a_single_revision_chain():
    from app.db import models  # noqa: F401

    assert set(Base.metadata.tables) == {f"app.{table}" for table in (
        "employees", "users", "sessions", "inquiries", "tickets", "alerts", "dlq")}
    script = ScriptDirectory.from_config(Config("migrations/alembic.ini"))
    assert script.get_heads() == ["0002"]
    assert [rev.revision for rev in script.walk_revisions()] == ["0002", "0001"]


def test_db_check_redacts_subprocess_failures(monkeypatch, capsys):
    from types import SimpleNamespace
    from deploy import check_db

    password = secrets.token_urlsafe(24)
    url = f"postgresql+psycopg://fixture:{password}@postgres/db"
    monkeypatch.setattr(check_db, "dotenv_values", lambda _: {
        "DATABASE_URL": url, "POSTGRES_PASSWORD": password, "POSTGRES_DB": "db", "POSTGRES_USER": "fixture",
    })
    monkeypatch.setattr("sys.argv", ["check_db.py"])
    monkeypatch.setattr(check_db.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        stdout=f"failed with {url}", stderr=f"password={password}", returncode=1,
    ))
    assert check_db.main() == 1
    output = capsys.readouterr().out
    assert password not in output
    assert url not in output
    assert "[REDACTED]" in output


def test_db_runner_refuses_a_url_pointing_outside_its_service(monkeypatch, capsys):
    from deploy import check_db

    monkeypatch.setattr("sys.argv", ["check_db.py", "--alembic", "upgrade"])
    private_input = secrets.token_urlsafe(24)
    monkeypatch.setattr(check_db, "dotenv_values", lambda _: {
        "DATABASE_URL": f"postgresql+psycopg://fixture:{private_input}@other-service/db",
        "POSTGRES_PASSWORD": private_input, "POSTGRES_USER": "fixture", "POSTGRES_DB": "db",
    })
    monkeypatch.setattr(check_db.subprocess, "run", lambda *a, **k: pytest.fail("must not run Docker"))
    assert check_db.main() == 1
    assert private_input not in capsys.readouterr().out
