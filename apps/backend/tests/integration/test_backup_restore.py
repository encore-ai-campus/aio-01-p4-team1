"""Opt-in logical backup/restore check using separate disposable databases."""

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


def _pgpass_field(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:")


def _table_counts(engine) -> dict[str, object]:
    inspector = inspect(engine)
    counts: dict[str, object] = {}
    with engine.connect() as connection:
        counts["alembic_version"] = connection.scalar(
            text("SELECT version_num FROM alembic_version"))
        for schema in ("app", "rag"):
            for table in sorted(inspector.get_table_names(schema=schema)):
                counts[f"{schema}.{table}"] = connection.scalar(
                    text(f'SELECT count(*) FROM "{schema}"."{table}"'))
        counts["rag_document_hashes"] = tuple(connection.execute(text(
            "SELECT doc_key, source_hash FROM rag.documents ORDER BY doc_key")).all())
        counts["rag_chunk_hashes"] = tuple(connection.execute(text("""
            SELECT document_id, chunk_no, content_hash, vector_dims(embedding)
            FROM rag.chunks ORDER BY document_id, chunk_no
        """)).all())
    return counts


@pytest.mark.integration
def test_full_backup_restores_to_separate_disposable_database():
    source_raw = os.environ.get("P1_4_BACKUP_SOURCE_URL")
    target_raw = os.environ.get("P1_4_BACKUP_RESTORE_URL")
    if (os.environ.get("P1_4_BACKUP_RESTORE_OPT_IN") != "I_ACCEPT_LOCAL_DISPOSABLE_TARGET"
            or not source_raw or not target_raw):
        pytest.skip("requires explicit opt-in and separate source/restore database URLs")
    if not shutil.which("pg_dump") or not shutil.which("pg_restore"):
        pytest.skip("pg_dump and pg_restore client tools are unavailable")

    source_url = make_url(source_raw)
    target_url = make_url(target_raw)
    if (source_url.database == target_url.database or
            not target_url.database.endswith("_p1_4_restore") or
            source_url.host != target_url.host or source_url.port != target_url.port):
        pytest.fail("restore target must be a different disposable DB ending in _p1_4_restore")
    source_engine = create_engine(source_url, pool_pre_ping=True)
    target_engine = create_engine(target_url, pool_pre_ping=True)
    try:
        target_inspector = inspect(target_engine)
        if target_inspector.get_table_names(schema="app") or target_inspector.get_table_names(schema="rag"):
            pytest.fail("restore target must be empty; no existing tables were changed")
        before = _table_counts(source_engine)
        with tempfile.TemporaryDirectory(prefix="p1-4-backup-") as temp_dir:
            temp_path = Path(temp_dir)
            archive = temp_path / "private-db.dump"
            passfile = temp_path / "pgpass"
            entries = []
            for url in (source_url, target_url):
                entries.append(":".join(_pgpass_field(str(value or "*")) for value in (
                    url.host, str(url.port or 5432), url.database, url.username,
                    url.password or "")))
            passfile.write_text("\n".join(entries) + "\n", encoding="utf-8")
            passfile.chmod(stat.S_IRUSR | stat.S_IWUSR)
            environment = {**os.environ, "PGPASSFILE": str(passfile)}
            dump_args = ["pg_dump", "--format=custom", "--no-owner", "--no-privileges",
                "--host", source_url.host, "--port", str(source_url.port or 5432),
                "--username", source_url.username, "--dbname", source_url.database,
                "--file", str(archive)]
            dumped = subprocess.run(dump_args, env=environment, capture_output=True, text=True)
            assert dumped.returncode == 0, "pg_dump failed; output suppressed to protect connection details"
            restore_args = ["pg_restore", "--exit-on-error", "--no-owner", "--no-privileges",
                "--host", target_url.host, "--port", str(target_url.port or 5432),
                "--username", target_url.username, "--dbname", target_url.database,
                str(archive)]
            restored = subprocess.run(restore_args, env=environment,
                                      capture_output=True, text=True)
            assert restored.returncode == 0, (
                "pg_restore failed; output suppressed; disposable target may need recreation")
        assert _table_counts(target_engine) == before
    finally:
        source_engine.dispose()
        target_engine.dispose()
