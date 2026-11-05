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


def list_tickets(session: Session) -> list[tuple[Ticket, Employee]]:
    return session.execute(select(Ticket, Employee)
        .join(Employee, Employee.id == Ticket.requester_id)
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())).all()


def get_assignee(session: Session, employee_id: int) -> Employee | None:
    return session.get(Employee, employee_id)


def get_ticket_by_id(session: Session, ticket_id: int) -> Ticket | None:
    return session.get(Ticket, ticket_id)
