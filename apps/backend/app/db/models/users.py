from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._types import CreatedAt, PrimaryKey


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('employee','admin')", name="role"), {"schema": "app"})

    id: Mapped[PrimaryKey]
    employee_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app.employees.id"), unique=True)
    login_id: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    must_change_password: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[CreatedAt]
