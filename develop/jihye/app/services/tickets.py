"""P1-3 ticket transactions and administrator operations."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import PublicApiError
from app.clients.practice_store import PracticeStoreClient
from app.core.config import Settings
from app.db.models import Employee, Ticket
from app.db.session import create_db_engine, create_session_factory
from app.repositories.tickets import (get_assignee, get_employee_by_name,
    get_inquiry_by_request_id, get_ticket_by_id, get_ticket_by_request_key, list_tickets)
from app.schemas.tickets import TicketCreate, TicketCreated, TicketPatch
from app.services.storage_mode import StorageMode, storage_mode


def _ticket_view(ticket: Ticket, employee: Employee) -> dict:
    return {
        "id": ticket.id, "ticket_id": ticket.ticket_id, "request_id": ticket.request_key,
        "requester": employee.name, "title": ticket.title, "category": ticket.category,
        "priority": ticket.priority, "status": ticket.status, "assignee": ticket.assignee_id,
        "reply": ticket.reply, "created_at": ticket.created_at, "updated_at": ticket.updated_at,
    }


def _existing_ticket(session: Session, request_key: str, requester_id: int) -> TicketCreated | None:
    existing = get_ticket_by_request_key(session, request_key)
    if existing is None:
        return None
    if existing.requester_id != requester_id:
        raise PublicApiError(403, "forbidden", "접근 권한이 없습니다.")
    return TicketCreated(ticket_id=existing.ticket_id, duplicate=True)


def create_ticket(settings: Settings, body: TicketCreate) -> TicketCreated:
    if storage_mode(settings) is StorageMode.PRACTICE:
        return PracticeStoreClient(settings).create_ticket(body)
    if not settings.database_url:
        raise PublicApiError(503, "service_unavailable", "티켓을 저장할 수 없습니다.")

    engine = create_db_engine(settings)
    try:
        try:
            with create_session_factory(engine).begin() as session:
                employee = get_employee_by_name(session, body.requester)
                if employee is None:
                    raise PublicApiError(400, "invalid_input", "직원 정보를 확인해 주세요.")
                inquiry = get_inquiry_by_request_id(session, body.key)
                if inquiry is not None and inquiry.requester_id != employee.id:
                    raise PublicApiError(403, "forbidden", "접근 권한이 없습니다.")
                duplicate = _existing_ticket(session, body.key, employee.id)
                if duplicate is not None:
                    return duplicate
                ticket = Ticket(request_key=body.key, inquiry_id=inquiry.id if inquiry else None,
                    requester_id=employee.id, title=body.title, category=body.category,
                    priority=body.priority)
                session.add(ticket)
                session.flush()
                return TicketCreated(ticket_id=ticket.ticket_id, duplicate=False)
        except IntegrityError:
            # The unique request_key constraint arbitrates concurrent first writes.
            with create_session_factory(engine).begin() as session:
                employee = get_employee_by_name(session, body.requester)
                existing = get_ticket_by_request_key(session, body.key)
                if employee is None or existing is None:
                    raise PublicApiError(503, "service_unavailable", "티켓을 저장할 수 없습니다.") from None
                return _existing_ticket(session, body.key, employee.id) or TicketCreated(
                    ticket_id=existing.ticket_id, duplicate=True)
    finally:
        engine.dispose()


def list_admin_tickets(settings: Settings) -> dict[str, list[dict]]:
    if storage_mode(settings) is StorageMode.PRACTICE:
        raise PublicApiError(503, "service_unavailable", "관리자 티켓 저장소를 사용할 수 없습니다.")
    if not settings.database_url:
        raise PublicApiError(503, "service_unavailable", "티켓을 조회할 수 없습니다.")
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            return {"items": [_ticket_view(ticket, employee)
                              for ticket, employee in list_tickets(session)]}
    finally:
        engine.dispose()


def update_admin_ticket(settings: Settings, *, ticket_id: int, body: TicketPatch) -> dict:
    if storage_mode(settings) is StorageMode.PRACTICE:
        raise PublicApiError(503, "service_unavailable", "관리자 티켓 저장소를 사용할 수 없습니다.")
    if not settings.database_url:
        raise PublicApiError(503, "service_unavailable", "티켓을 수정할 수 없습니다.")
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            ticket = get_ticket_by_id(session, ticket_id)
            if ticket is None:
                raise PublicApiError(404, "not_found", "티켓을 찾을 수 없습니다.")
            if "assignee" in body.model_fields_set:
                if body.assignee is None:
                    ticket.assignee_id = None
                else:
                    assignee = get_assignee(session, body.assignee)
                    if assignee is None or assignee.dept != "IT팀":
                        raise PublicApiError(400, "invalid_input", "담당자 정보를 확인해 주세요.")
                    ticket.assignee_id = assignee.id
            if "reply" in body.model_fields_set:
                ticket.reply = body.reply
            ticket.status = body.status
            ticket.updated_at = datetime.now(timezone.utc)
            session.flush()
            employee = session.get(Employee, ticket.requester_id)
            if employee is None:
                raise PublicApiError(503, "service_unavailable", "티켓 정보를 확인할 수 없습니다.")
            return _ticket_view(ticket, employee)
    finally:
        engine.dispose()
