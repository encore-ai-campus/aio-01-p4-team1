from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._types import PrimaryKey


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_id", "user_id"),
                      Index("ix_sessions_expires_at", "expires_at"), {"schema": "app"})

    id: Mapped[PrimaryKey]
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app.users.id"))
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
