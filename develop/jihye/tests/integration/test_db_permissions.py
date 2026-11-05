"""Check actual database role grants and denial boundaries."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db.session import create_db_engine

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires the isolated Compose DB",
)]


def test_role_grants_and_write_denials():
    engine = create_db_engine()
    try:
        with engine.connect() as db:
            for role in ("oke_app", "oke_rag_index", "oke_rag_search"):
                assert db.scalar(text("SELECT rolcanlogin FROM pg_roles WHERE rolname=:role"), {"role": role}) is False
            privileges = {
                ("oke_app", "app.tickets", "INSERT"): True,
                ("oke_app", "rag.chunks", "INSERT"): False,
                ("oke_rag_index", "rag.documents", "INSERT"): True,
                ("oke_rag_index", "rag.chunks", "INSERT"): True,
                ("oke_rag_search", "rag.chunks", "SELECT"): True,
                ("oke_rag_search", "rag.chunks", "INSERT"): False,
                ("oke_rag_search", "app.tickets", "SELECT"): False,
            }
            for (role, relation, privilege), expected in privileges.items():
                assert db.scalar(text("SELECT has_table_privilege(:role,:relation,:privilege)"),
                                 dict(role=role, relation=relation, privilege=privilege)) is expected
            assert db.scalar(text("SELECT has_schema_privilege('oke_app','rag','CREATE')")) is False
            assert db.scalar(text("SELECT has_sequence_privilege('oke_rag_index','rag.chunks_id_seq','USAGE')")) is True
            assert db.scalar(text("SELECT has_sequence_privilege('oke_rag_search','rag.chunks_id_seq','USAGE')")) is False
            with db.begin_nested():
                db.execute(text("SET LOCAL ROLE oke_rag_search"))
                assert db.scalar(text("SELECT count(*) FROM rag.chunks")) >= 0
                with pytest.raises(ProgrammingError):
                    with db.begin_nested():
                        db.execute(text("INSERT INTO rag.chunks DEFAULT VALUES"))
                with pytest.raises(ProgrammingError):
                    with db.begin_nested():
                        db.execute(text("CREATE TABLE rag.fixture_forbidden (id integer)"))
    finally:
        engine.dispose()
