from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })


def include_migration_name(name: str | None, type_: str, parent_names: dict) -> bool:
    """Limit autogenerate's reflected candidates to our app/rag schemas."""
    if type_ == "schema":
        return name in {"app", "rag"}
    return parent_names.get("schema_name") in {"app", "rag"}
