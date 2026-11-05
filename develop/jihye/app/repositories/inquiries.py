from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Inquiry


def get_by_request_id(session: Session, request_id: str) -> Inquiry | None:
    return session.scalar(select(Inquiry).where(Inquiry.request_id == request_id))


def list_by_requester(session: Session, requester_id: int) -> list[Inquiry]:
    return list(session.scalars(select(Inquiry).where(Inquiry.requester_id == requester_id)
        .order_by(Inquiry.created_at.desc(), Inquiry.id.desc())))
