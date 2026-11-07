"""Ticket persistence queries; ownership decisions stay in the service layer."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Employee, Inquiry, Ticket


def get_employee_by_name(session: Session, name: str) -> Employee | None:
    return session.scalar(select(Employee).where(Employee.name == name))


def get_inquiry_by_request_id(session: Session, request_id: str) -> Inquiry | None:
    return session.scalar(select(Inquiry).where(Inquiry.request_id == request_id))


def get_ticket_by_request_key(session: Session, request_key: str) -> Ticket | None:
    return session.scalar(select(Ticket).where(Ticket.request_key == request_key))


def get_ticket_by_external_id(session: Session, ticket_id: str) -> Ticket | None:
    return session.scalar(select(Ticket).where(Ticket.ticket_id == ticket_id))


def list_tickets(session: Session) -> list[tuple[Ticket, Employee, str | None]]:
    return session.execute(select(Ticket, Employee, Inquiry.question)
        .join(Employee, Employee.id == Ticket.requester_id)
        .outerjoin(Inquiry, (Inquiry.request_id == Ticket.request_key)
            & (Inquiry.requester_id == Ticket.requester_id)
            & ((Inquiry.id == Ticket.inquiry_id) | Ticket.inquiry_id.is_(None)))
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())).all()


def get_ticket_question(session: Session, ticket: Ticket) -> str | None:
    """Return only the inquiry that matches this ticket's key, owner and optional FK."""
    statement = select(Inquiry.question).where(
        Inquiry.request_id == ticket.request_key,
        Inquiry.requester_id == ticket.requester_id,
    )
    if ticket.inquiry_id is not None:
        statement = statement.where(Inquiry.id == ticket.inquiry_id)
    return session.scalar(statement)


def get_assignee(session: Session, employee_id: int) -> Employee | None:
    return session.get(Employee, employee_id)


def get_ticket_by_id(session: Session, ticket_id: int) -> Ticket | None:
    return session.get(Ticket, ticket_id)
