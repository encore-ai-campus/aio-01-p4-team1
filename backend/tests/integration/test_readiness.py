"""Readiness failure boundaries plus opt-in real PostgreSQL verification."""

import os
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import create_db_engine
from app.main import create_app
from app.services import readiness


def test_liveness_and_missing_db_settings():
    with TestClient(create_app(Settings(database_url=None))) as client:
        assert client.get("/health/live").status_code == 200
        result = client.get("/health/ready")
        assert result.status_code == 503
        assert result.json()["reason"] == "database_unavailable"


@pytest.mark.parametrize("versions,vector,shape,reason", [
    (["0004"], True, "vector(3072)", "schema_not_current"),
    ([], True, "vector(3072)", "schema_not_current"),
    (["0005"], False, "vector(3072)", "vector_missing"),
    (["0005"], True, "vector(3071)", "vector_schema_mismatch"),
    (["0005"], True, "vector(3072)", "ok"),
])
def test_readiness_prerequisites(monkeypatch, versions, vector, shape, reason):
    db = MagicMock()
    db.scalars.return_value = versions
    db.scalar.side_effect = [vector, shape]
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = db
    monkeypatch.setattr(readiness, "create_db_engine", lambda *args, **kwargs: engine)
    result = readiness.check_database(Settings())
    assert result["reason"] == reason
    engine.dispose.assert_called_once()


def test_db_error_does_not_leak(monkeypatch):
    def fail(*args, **kwargs):
        raise OperationalError("sensitive-url", {}, Exception("sensitive-password"))
    monkeypatch.setattr(readiness, "create_db_engine", fail)
    with TestClient(create_app()) as client:
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert "sensitive" not in response.text
        assert client.get("/health/live").status_code == 200


@pytest.mark.integration
@pytest.mark.skipif(os.environ.get("OKE_RUN_DB_TESTS") != "1", reason="requires isolated DB")
def test_real_db_and_application_role():
    with TestClient(create_app()) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready", "reason": "ok", "scope": "database", "service_mode": "app"}
    engine = create_db_engine()
    try:
        with engine.connect() as db:
            db.execute(text("SET LOCAL ROLE oke_app"))
            assert db.scalar(text("SELECT version_num FROM public.alembic_version")) == "0005"
            assert not db.scalar(text("SELECT has_table_privilege(current_user,'public.alembic_version','UPDATE')"))
    finally:
        engine.dispose()
