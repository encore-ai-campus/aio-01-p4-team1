from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._types import PrimaryKey


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = {"schema": "app"}

    id: Mapped[PrimaryKey]
    name: Mapped[str] = mapped_column(Text, unique=True)
    dept: Mapped[str] = mapped_column(Text)
