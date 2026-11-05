"""P1-3 alert and DLQ writes, each committed independently."""

import re
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.api.errors import PublicApiError
from app.clients.practice_store import PracticeStoreClient
from app.core.config import Settings
from app.db.models import Alert, Dlq, Ticket
from app.db.session import create_db_engine, create_session_factory
from app.repositories.alerts import count_alerts, get_by_event_key, list_alerts
from app.repositories.dlq import count_dlq
from app.repositories.tickets import get_ticket_by_external_id
from app.schemas.alerts import AlertCreate, AlertStoredResponse, DlqCreate, StoredResponse
from app.services.storage_mode import StorageMode, storage_mode

_PRIVATE_PATTERNS = (
    re.compile(r"\bBearer\s+[^\s,;]+", re.IGNORECASE),
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b\d{6}[- ]?\d{7}\b"),
    re.compile(r"(?:\+82[\s.-]?(?:0)?(?:1[016789]|2|[3-6]\d)|0(?:1[016789]|2|[3-6]\d))[\s.-]?\d{3,4}[\s.-]?\d{4}"),
    re.compile(r"((?:password|passwd|token|api[_-]?key|secret|authorization|cookie|session|비밀번호|암호)\s*[:=]\s*)[^\s,;]+", re.IGNORECASE),
)
_SECRET_KEYS = re.compile(r"password|passwd|token|api[_-]?key|secret|authorization|cookie|session|비밀번호|암호", re.IGNORECASE)


def _mask_text(value: str) -> str:
    safe = value
    for pattern in _PRIVATE_PATTERNS:
        if pattern.groups:
            safe = pattern.sub(lambda match: match.group(1) + "[REDACTED]", safe)
        else:
            safe = pattern.sub("[REDACTED]", safe)
    return safe


def sanitize_safe_payload(value: Any) -> Any:
    """Defensively remove obvious credentials and personal contact data before persistence."""
    if isinstance(value, dict):
        return {str(key): ("[REDACTED]" if _SECRET_KEYS.search(str(key)) else sanitize_safe_payload(item))
                for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_safe_payload(item) for item in value]
    if isinstance(value, str):
        return _mask_text(value)
    return value


def create_alert(settings: Settings, body: AlertCreate) -> AlertStoredResponse:
    if storage_mode(settings) is StorageMode.PRACTICE:
        return PracticeStoreClient(settings).create_alert(body)
    if not settings.database_url:
        raise PublicApiError(503, "service_unavailable", "알림을 저장할 수 없습니다.")
    engine = create_db_engine(settings)
    try:
        try:
            with create_session_factory(engine).begin() as session:
                ticket = None
                if body.ticket_id is not None:
                    ticket = get_ticket_by_external_id(session, body.ticket_id)
                    if ticket is None:
                        raise PublicApiError(404, "not_found", "티켓을 찾을 수 없습니다.")
                if body.event_key is not None:
                    existing = get_by_event_key(session, body.event_key)
                    if existing is not None:
                        return AlertStoredResponse(stored=0, count=count_alerts(session), duplicate=True)
                alert = Alert(ticket_id=ticket.id if ticket else None, event_key=body.event_key,
                    workflow=body.workflow, node=body.node, message=_mask_text(body.message),
                    severity=body.severity)
                session.add(alert)
                session.flush()
                return AlertStoredResponse(stored=1, count=count_alerts(session), duplicate=False)
        except IntegrityError:
            # A nullable unique event_key arbitrates concurrent duplicate requests.
            if body.event_key is None:
                raise PublicApiError(503, "service_unavailable", "알림을 저장할 수 없습니다.") from None
            with create_session_factory(engine).begin() as session:
                existing = get_by_event_key(session, body.event_key)
                if existing is None:
                    raise PublicApiError(503, "service_unavailable", "알림을 저장할 수 없습니다.") from None
                return AlertStoredResponse(stored=0, count=count_alerts(session), duplicate=True)
    finally:
        engine.dispose()


def create_dlq(settings: Settings, body: DlqCreate) -> StoredResponse:
    if storage_mode(settings) is StorageMode.PRACTICE:
        return PracticeStoreClient(settings).create_dlq(body)
    if not settings.database_url:
        raise PublicApiError(503, "service_unavailable", "오류 기록을 저장할 수 없습니다.")
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            row = Dlq(request_id=body.request_id, execution_ref=body.execution_ref,
                workflow=body.workflow, node=body.node, reason=_mask_text(body.reason),
                safe_payload=sanitize_safe_payload(body.safe_payload), status="pending")
            session.add(row)
            session.flush()
            return StoredResponse(stored=1, count=count_dlq(session))
    finally:
        engine.dispose()


def list_admin_alerts(settings: Settings) -> dict[str, list[dict]]:
    if storage_mode(settings) is StorageMode.PRACTICE:
        raise PublicApiError(503, "service_unavailable", "관리자 알림 저장소를 사용할 수 없습니다.")
    if not settings.database_url:
        raise PublicApiError(503, "service_unavailable", "알림을 조회할 수 없습니다.")
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            items = []
            for alert, external_ticket_id in list_alerts(session):
                items.append({"id": alert.id, "ticket_id": external_ticket_id,
                    "workflow": alert.workflow, "node": alert.node, "message": alert.message,
                    "severity": alert.severity, "created_at": alert.created_at})
            return {"items": items}
    finally:
        engine.dispose()
