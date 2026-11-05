"""Inquiry pre-save, short DB transactions, C02 call, then safe result persistence."""

from uuid import uuid4

import anyio
from sqlalchemy.exc import IntegrityError

from app.api.errors import PublicApiError
from app.clients.support import build_support_client
from app.core.config import Settings
from app.db.models import Inquiry
from app.db.session import create_db_engine, create_session_factory
from app.repositories.inquiries import get_by_request_id, list_by_requester
from app.repositories.users import get_user_identity
from app.schemas.auth import UserSummary
from app.schemas.support import AskRequest, SupportRequest, SupportResponse


def _prepare(settings: Settings, *, request_id: str, body: AskRequest,
             principal: UserSummary) -> int:
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            identity = get_user_identity(session, principal.id)
            if identity is None:
                raise PublicApiError(401, "unauthorized", "로그인이 필요합니다.")
            user, employee = identity
            if not user.is_active:
                raise PublicApiError(401, "unauthorized", "로그인이 필요합니다.")
            existing = get_by_request_id(session, request_id)
            if existing is not None:
                _check_owner_and_payload(existing, employee.id, body)
                existing.status = "submitted"
                session.flush()
                return employee.id
            inquiry = Inquiry(request_id=request_id, requester_id=employee.id,
                question=body.question, attempt=body.attempt, context=body.context,
                status="submitted")
            session.add(inquiry)
            session.flush()
            return employee.id
    except IntegrityError:
        # A competing insert won the unique request_id. Re-check its owner before any C02 call.
        with create_session_factory(engine).begin() as session:
            identity = get_user_identity(session, principal.id)
            existing = get_by_request_id(session, request_id)
            if identity is None or existing is None:
                raise PublicApiError(503, "service_unavailable",
                                     "문의를 저장할 수 없습니다.") from None
            user, employee = identity
            if not user.is_active:
                raise PublicApiError(401, "unauthorized", "로그인이 필요합니다.")
            _check_owner_and_payload(existing, employee.id, body)
            existing.status = "submitted"
            session.flush()
            return employee.id
    finally:
        engine.dispose()


def _check_owner_and_payload(inquiry: Inquiry, requester_id: int, body: AskRequest) -> None:
    if inquiry.requester_id != requester_id:
        raise PublicApiError(403, "forbidden", "접근 권한이 없습니다.")
    if (inquiry.question != body.question or inquiry.attempt != body.attempt
            or inquiry.context != body.context):
        raise PublicApiError(409, "conflict", "요청 ID가 기존 문의 내용과 다릅니다.")


def _save_result(settings: Settings, *, request_id: str, requester_id: int,
                 result: SupportResponse) -> None:
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            inquiry = get_by_request_id(session, request_id)
            if inquiry is None or inquiry.requester_id != requester_id:
                raise PublicApiError(503, "service_unavailable", "문의 결과를 저장할 수 없습니다.")
            inquiry.result = result.model_dump(mode="json", exclude_unset=True)
            inquiry.status = "completed"
            session.flush()
    finally:
        engine.dispose()


def _mark_failed(settings: Settings, *, request_id: str, requester_id: int) -> None:
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            inquiry = get_by_request_id(session, request_id)
            if inquiry is not None and inquiry.requester_id == requester_id:
                inquiry.status = "failed"
                session.flush()
    finally:
        engine.dispose()


def _list_requests(settings: Settings, user_id: int) -> list[dict]:
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            identity = get_user_identity(session, user_id)
            if identity is None or not identity[0].is_active:
                raise PublicApiError(401, "unauthorized", "로그인이 필요합니다.")
            employee_id = identity[1].id
            rows = list_by_requester(session, employee_id)
            return [{"request_id": row.request_id, "question": row.question,
                     "attempt": row.attempt, "result": row.result,
                     "ticket": row.result.get("ticket") if row.result else None,
                     "created_at": row.created_at} for row in rows]
    finally:
        engine.dispose()


async def ask_support(settings: Settings, *, body: AskRequest,
                      principal: UserSummary) -> SupportResponse:
    request_id = body.request_id or uuid4().hex
    requester_id = await anyio.to_thread.run_sync(
        lambda: _prepare(settings, request_id=request_id, body=body, principal=principal))
    outgoing = SupportRequest(request_id=request_id, user=principal.name,
        question=body.question, channel="web", attempt=body.attempt, context=body.context)
    try:
        result = await build_support_client(settings).ask(outgoing)
        await anyio.to_thread.run_sync(lambda: _save_result(settings, request_id=request_id,
            requester_id=requester_id, result=result))
        return result
    except Exception:
        # Support 400s and transport failures stay public-safe; failed rows remain retryable.
        await anyio.to_thread.run_sync(lambda: _mark_failed(settings, request_id=request_id,
                                                             requester_id=requester_id))
        raise


def my_requests(settings: Settings, *, user_id: int) -> dict[str, list[dict]]:
    return {"items": _list_requests(settings, user_id)}
