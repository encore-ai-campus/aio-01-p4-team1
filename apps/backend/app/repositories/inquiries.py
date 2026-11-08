from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Inquiry, Ticket


def get_by_request_id(session: Session, request_id: str) -> Inquiry | None:
    return session.scalar(select(Inquiry).where(Inquiry.request_id == request_id))


def list_by_requester(session: Session, requester_id: int) -> list[Inquiry]:
    return list(session.scalars(select(Inquiry).where(Inquiry.requester_id == requester_id)
        .order_by(Inquiry.created_at.desc(), Inquiry.id.desc())))


def list_linked_tickets(session: Session, *, requester_id: int,
                        inquiries: list[Inquiry]) -> list[Ticket]:
    """Return only tickets linked to these owned inquiries through all three identity keys."""
    if not inquiries:
        return []
    inquiry_ids = [inquiry.id for inquiry in inquiries]
    return list(session.scalars(select(Ticket).join(
        Inquiry, Ticket.inquiry_id == Inquiry.id).where(
            Inquiry.id.in_(inquiry_ids),
            Inquiry.requester_id == requester_id,
            Ticket.requester_id == requester_id,
            Ticket.request_key == Inquiry.request_id,
        )))
