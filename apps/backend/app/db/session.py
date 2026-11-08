from pydantic import SecretStr
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import Pool, QueuePool

from app.core.config import Settings


class DatabaseConfigurationError(ValueError):
    """Safe configuration error: never embeds the input DSN."""


def database_url(value: SecretStr | str | None) -> URL:
    try:
        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        if not raw:
            raise ValueError
        url = make_url(raw)
        if (url.drivername != "postgresql+psycopg" or not url.host or not url.database
                or not url.username or not url.password):
            raise ValueError
        # P0-3 uses the explicitly selected psycopg driver.
        _ = url.port
        return url
    except Exception:
        raise DatabaseConfigurationError(
            "DATABASE_URL must be a postgresql+psycopg URL with host, database and credentials"
        ) from None


def create_db_engine(settings: Settings | None = None, *, poolclass: type[Pool] = QueuePool) -> Engine:
    selected = settings if settings is not None else Settings()
    return create_engine(
        database_url(selected.database_url),
        connect_args={"connect_timeout": 3},
        pool_pre_ping=True,
        hide_parameters=True,
        echo=False,
        poolclass=poolclass,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
