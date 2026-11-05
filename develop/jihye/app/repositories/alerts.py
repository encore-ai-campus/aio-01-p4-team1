"""Alert persistence queries."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Alert, Ticket


def get_by_event_key(session: Session, event_key: str) -> Alert | None:
    return session.scalar(select(Alert).where(Alert.event_key == event_key))


def count_alerts(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(Alert)) or 0)


def list_alerts(session: Session) -> list[tuple[Alert, str | None]]:
    return session.execute(select(Alert, Ticket.ticket_id)
        .outerjoin(Ticket, Ticket.id == Alert.ticket_id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())).all()
