"""Opt-in backup/restore check for the private local Compose PostgreSQL only."""

import argparse
import subprocess
import uuid
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent
CONTAINER = "oke-jihye-p0-postgres-1"
SOURCE_DB = "oke_jihye_p0"
TARGET_DB = "oke_jihye_p1_4_restore"

SNAPSHOT_SQL = """
SELECT jsonb_build_object(
  'server_version', current_setting('server_version'),
  'vector_version', (SELECT extversion FROM pg_extension WHERE extname = 'vector'),
  'revision', (SELECT version_num FROM public.alembic_version),
  'tables', jsonb_build_object(
    'app.employees', (SELECT count(*) FROM app.employees),
    'app.users', (SELECT count(*) FROM app.users),
    'app.sessions', (SELECT count(*) FROM app.sessions),
    'app.inquiries', (SELECT count(*) FROM app.inquiries),
    'app.tickets', (SELECT count(*) FROM app.tickets),
    'app.alerts', (SELECT count(*) FROM app.alerts),
    'app.dlq', (SELECT count(*) FROM app.dlq),
    'rag.documents', (SELECT count(*) FROM rag.documents),
    'rag.chunks', (SELECT count(*) FROM rag.chunks)
  ),
  'document_hashes', COALESCE(
    (SELECT jsonb_agg(jsonb_build_array(doc_key, source_hash) ORDER BY doc_key)
     FROM rag.documents), '[]'::jsonb),
  'chunk_hashes_and_dimensions', COALESCE(
    (SELECT jsonb_agg(jsonb_build_array(document_id, chunk_no, content_hash,
                                         vector_dims(embedding))
                      ORDER BY document_id, chunk_no)
     FROM rag.chunks), '[]'::jsonb),
  'embedding_type', (SELECT format_type(attribute.atttypid, attribute.atttypmod)
                     FROM pg_attribute AS attribute
                     WHERE attribute.attrelid = 'rag.chunks'::regclass
                       AND attribute.attname = 'embedding'
                       AND NOT attribute.attisdropped)
)::text;
"""


def _container_shell(script: str, *arguments: str) -> list[str]:
    return ["docker", "exec", CONTAINER, "sh", "-c", script, "sh", *arguments]


def _run(label: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        print(f"{label}: failed (details suppressed)")
    return result


def _psql(database: str, sql: str) -> str:
    result = _run("read-only DB query", _container_shell(
        'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -A -t -v ON_ERROR_STOP=1 '
        '-U "$POSTGRES_USER" -d "$1" -c "$2"', database, sql))
    if result.returncode:
        raise RuntimeError("database query failed")
    return result.stdout.strip()


def _validate_private_settings(values: dict[str, str | None]) -> None:
    raw_url = values.get("DATABASE_URL")
    try:
        url = make_url(raw_url or "")
        if (url.drivername != "postgresql+psycopg" or url.host != "postgres"
                or url.database != SOURCE_DB or values.get("POSTGRES_DB") != SOURCE_DB
                or url.username != values.get("POSTGRES_USER")
                or url.password != values.get("POSTGRES_PASSWORD")
                or url.username != "oke_migration"):
            raise ValueError
    except Exception:
        raise RuntimeError("backup check is restricted to the private local Compose DB") from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-private-db", action="store_true",
                        help="confirm source is only deploy/compose.yaml's private local DB")
    args = parser.parse_args()
    if not args.confirm_private_db:
        parser.error("pass --confirm-private-db only for the isolated local Compose DB")

    values = dotenv_values(ROOT / "deploy/.env")
    try:
        _validate_private_settings(values)
        version_script = 'pg_dump --version && pg_restore --version'
        versions = _run("pg client version check", _container_shell(version_script))
        if versions.returncode:
            return 1
        version_lines = versions.stdout.strip().splitlines()
        if (len(version_lines) != 2 or "16." not in version_lines[0]
                or "16." not in version_lines[1]):
            print("pg_dump/pg_restore major version must match the local PostgreSQL 16 server")
            return 1
        print("pg_dump/pg_restore: PostgreSQL 16 client tools available in the private DB container")

        exists = _psql("postgres", f"SELECT count(*) FROM pg_database WHERE datname = '{TARGET_DB}'")
        if exists != "0":
            print("restore target already exists; no existing database was modified")
            return 1

        current_revision = _psql(SOURCE_DB, "SELECT version_num FROM public.alembic_version")
        if current_revision != "0005":
            print("source revision is not the expected local head 0005")
            return 1
        before = _psql(SOURCE_DB, SNAPSHOT_SQL)
        if not before:
            print("source snapshot could not be read")
            return 1

        archive = f"/tmp/p1-4-backup-{uuid.uuid4().hex}.dump"
        target_created = False
        success = False
        cleanup_failed = False
        try:
            dump = _run("pg_dump", _container_shell(
                'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump --format=custom --no-owner '
                '--no-privileges --username "$POSTGRES_USER" --dbname "$1" --file "$2"',
                SOURCE_DB, archive))
            if dump.returncode:
                raise RuntimeError("pg_dump failed")

            created = _run("restore DB creation", _container_shell(
                'PGPASSWORD="$POSTGRES_PASSWORD" createdb --username "$POSTGRES_USER" '
                '--template=template0 "$1"', TARGET_DB))
            if created.returncode:
                raise RuntimeError("restore DB creation failed")
            target_created = True
            print("created empty, disposable local restore database")

            restored = _run("pg_restore", _container_shell(
                'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore --exit-on-error '
                '--single-transaction --no-owner --no-privileges '
                '--username "$POSTGRES_USER" --dbname "$1" "$2"', TARGET_DB, archive))
            if restored.returncode:
                raise RuntimeError("pg_restore failed")
            after = _psql(TARGET_DB, SNAPSHOT_SQL)
            if before != after:
                raise RuntimeError("restored snapshot differs from source")
            print("backup/restore comparison: revision, table counts, document/chunk hashes, vector dimensions match")
            success = True
        finally:
            if target_created:
                dropped = _run("restore DB cleanup", _container_shell(
                    'PGPASSWORD="$POSTGRES_PASSWORD" dropdb --username "$POSTGRES_USER" "$1"',
                    TARGET_DB))
                if dropped.returncode == 0:
                    print("temporary restore database removed; source database retained")
                else:
                    cleanup_failed = True
            archived = _run("temporary archive cleanup",
                             _container_shell("rm -f -- \"$1\"", archive))
            if archived.returncode:
                cleanup_failed = True
        if cleanup_failed:
            print("temporary artifact cleanup failed; inspect only the local disposable target")
        return 0 if success and not cleanup_failed else 1
    except RuntimeError as error:
        print(str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
