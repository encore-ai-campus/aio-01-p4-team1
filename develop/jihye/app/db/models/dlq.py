from typing import Any

from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._types import CreatedAt, PrimaryKey


class Dlq(Base):
    __tablename__ = "dlq"
    __table_args__ = (Index("ix_dlq_request_id", "request_id"),
                      Index("ix_dlq_execution_ref", "execution_ref"), {"schema": "app"})

    id: Mapped[PrimaryKey]
    request_id: Mapped[str | None] = mapped_column(Text)
    execution_ref: Mapped[str | None] = mapped_column(Text)
    workflow: Mapped[str] = mapped_column(Text)
    node: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    safe_payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
