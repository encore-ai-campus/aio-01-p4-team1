from datetime import datetime

from sqlalchemy import (BigInteger, CheckConstraint, DateTime, ForeignKey, Index,
                        Sequence, Text, func, text)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._types import CreatedAt, PrimaryKey

ticket_number_sequence = Sequence("ticket_number_seq", start=2001, schema="app",
                                  metadata=Base.metadata, data_type=BigInteger())


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("char_length(request_key) BETWEEN 1 AND 64", name="request_key_length"),
        CheckConstraint("priority IN ('normal','high')", name="priority"),
        CheckConstraint("status IN ('open','in_progress','resolved')", name="status"),
        Index("ix_tickets_inquiry_id", "inquiry_id"),
        Index("ix_tickets_requester_id", "requester_id"),
        Index("ix_tickets_assignee_id", "assignee_id"),
        Index("ix_tickets_status_created_at", "status", "created_at"),
        {"schema": "app"},
    )

    id: Mapped[PrimaryKey]
    ticket_id: Mapped[str] = mapped_column(
        Text, unique=True, server_default=text("'T-' || nextval('app.ticket_number_seq'::regclass)::text"))
    request_key: Mapped[str] = mapped_column(Text, unique=True)
    inquiry_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("app.inquiries.id"))
    requester_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app.employees.id"))
    title: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=text("'open'"))
    assignee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("app.employees.id"))
    reply: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                onupdate=func.now())
