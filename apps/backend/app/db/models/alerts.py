from sqlalchemy import BigInteger, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._types import CreatedAt, PrimaryKey


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_ticket_id", "ticket_id"),
                      Index("ix_alerts_created_at", "created_at"), {"schema": "app"})

    id: Mapped[PrimaryKey]
    ticket_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("app.tickets.id"))
    event_key: Mapped[str | None] = mapped_column(Text, unique=True)
    workflow: Mapped[str] = mapped_column(Text)
    node: Mapped[str] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text)
    created_at: Mapped[CreatedAt]
