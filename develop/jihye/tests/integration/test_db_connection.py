"""Read-only P0-3 checks. Explicit opt-in; never select a default/shared DB."""

import io
import os
import secrets

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.db.session import create_db_engine, create_session_factory, database_url

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="run via the isolated deploy/check_db.py or explicitly opt in with DATABASE_URL",
)]


@pytest.fixture
def engine():
    instance = create_db_engine()
    yield instance
    instance.dispose()


def test_database_connection_and_session(engine):
    with create_session_factory(engine)() as session:
        assert session.scalar(text("SELECT 1")) == 1
        expected = database_url(Settings().database_url).database
        assert session.scalar(text("SELECT current_database()")) == expected


def test_pgvector_is_available_but_not_applied_in_p0_3(engine):
    with engine.connect() as connection:
        available = connection.scalar(text("SELECT default_version FROM pg_available_extensions WHERE name='vector'"))
        assert available
        assert connection.scalar(text("SELECT count(*) FROM pg_extension WHERE extname='vector'")) == 0


def test_no_application_schemas_or_tables_yet(engine):
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM pg_namespace WHERE nspname IN ('app','rag')")) == 0


def test_wrong_password_is_actually_rejected():
    url = database_url(Settings().database_url).set(password=secrets.token_urlsafe(36))
    wrong = create_db_engine(Settings(database_url=url.render_as_string(hide_password=False)))
    try:
        with pytest.raises(OperationalError) as caught:
            with wrong.connect():
                pass
        # libpq startup authentication failures may not expose a SQLSTATE.
        assert caught.value.orig.sqlstate in {"28P01", None}
        assert "password authentication failed" in str(caught.value.orig).lower()
    finally:
        wrong.dispose()


def test_alembic_current_has_no_revision(engine):
    output = io.StringIO()
    command.current(Config("migrations/alembic.ini", stdout=output))
    assert output.getvalue().strip() == ""
