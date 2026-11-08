"""Read-only database readiness; never calls external workflow services."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.db.session import DatabaseConfigurationError, create_db_engine

ROOT = Path(__file__).resolve().parents[2]


def check_database(settings: Settings) -> dict[str, str]:
    engine = None
    try:
        cfg = Config(str(ROOT / "migrations/alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        expected = ScriptDirectory.from_config(cfg).get_heads()
        if len(expected) != 1:
            return {"status": "unavailable", "reason": "schema_not_current"}
        engine = create_db_engine(settings, poolclass=NullPool)
        with engine.connect() as db:
            db.execute(text("SET LOCAL statement_timeout = '2000ms'"))
            db.execute(text("SELECT 1"))
            versions = list(db.scalars(text("SELECT version_num FROM public.alembic_version")))
            if sorted(versions) != sorted(expected):
                return {"status": "unavailable", "reason": "schema_not_current"}
            if not db.scalar(text("SELECT EXISTS (SELECT FROM pg_extension WHERE extname='vector')")):
                return {"status": "unavailable", "reason": "vector_missing"}
            if db.scalar(text("""SELECT format_type(a.atttypid,a.atttypmod)
                FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
                JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='rag' AND c.relname='chunks' AND a.attname='embedding'
                  AND NOT a.attisdropped""")) != "vector(3072)":
                return {"status": "unavailable", "reason": "vector_schema_mismatch"}
        return {"status": "ready", "reason": "ok"}
    except (SQLAlchemyError, DatabaseConfigurationError):
        return {"status": "unavailable", "reason": "database_unavailable"}
    finally:
        if engine is not None:
            engine.dispose()
