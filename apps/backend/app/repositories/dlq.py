"""Dead-letter persistence queries."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Dlq


def count_dlq(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(Dlq)) or 0)
