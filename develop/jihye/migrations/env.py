"""Alembic environment: no application DDL, bootstrap or external HTTP here."""

from alembic import context
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.base import Base, include_migration_name
from app.db.session import create_db_engine, database_url
from app.db import models  # noqa: F401 -- register app tables for autogenerate

# P0-4 app models are registered; P0-5 will add rag models.
target_metadata = Base.metadata


def configure(**kwargs):
    context.configure(
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_migration_name,
        compare_type=True,
        compare_server_default=True,
        # Bookkeeping only: application DDL is limited to app/rag.
        version_table_schema="public",
        **kwargs,
    )


def run_migrations_offline():
    configure(url=database_url(Settings().database_url), literal_binds=True,
              dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_db_engine(poolclass=NullPool)
    try:
        with engine.connect() as connection:
            configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    except SQLAlchemyError:
        # Do not print exception text, SQL parameters or credentials in CLI output.
        raise RuntimeError("Database migration command failed; inspect a sanitized DB check") from None
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
