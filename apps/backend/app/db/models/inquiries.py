from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._types import CreatedAt, PrimaryKey


class Inquiry(Base):
    __tablename__ = "inquiries"
    __table_args__ = (
        CheckConstraint("char_length(request_id) BETWEEN 1 AND 64", name="request_id_length"),
        CheckConstraint("char_length(question) BETWEEN 1 AND 500", name="question_length"),
        CheckConstraint("attempt >= 1", name="attempt"),
        Index("ix_inquiries_requester_id_created_at", "requester_id", "created_at"),
        {"schema": "app"},
    )

    id: Mapped[PrimaryKey]
    request_id: Mapped[str] = mapped_column(Text, unique=True)
    requester_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app.employees.id"))
    question: Mapped[str] = mapped_column(Text)
    attempt: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    context: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Workflow state names/defaults are assigned by the future service, not this DDL.
    status: Mapped[str] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
