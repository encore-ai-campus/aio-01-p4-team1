"""Exercise browser inquiry persistence and C05 ticket linkage on isolated PostgreSQL."""

import json
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, select

from app.clients.support import SupportClient
from app.core.config import Settings
from app.core.security import hash_session_token, new_session_token
from app.db.models import Employee, Inquiry, Session as LoginSession, Ticket, User
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from app.services import inquiries as inquiry_service

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires the isolated Compose DB opt-in",
)]


def test_session_inquiry_support_and_c05_ticket_linkage(monkeypatch):
    engine = create_db_engine()
    suffix = uuid4().hex[:12]
    request_id = f"p14-web-{suffix}"
    employee_name = f"p14-user-{suffix}"
    token = new_session_token()
    session_secret = "p1-4-local-session-fixture"
    internal_key = "p1-4-local-internal-fixture"
    seen = []
    # Remove only stale fixtures from this test after an interrupted prior run.
    with create_session_factory(engine).begin() as session:
        stale_inquiries = select(Inquiry.id).where(Inquiry.request_id.like("p14-web-%"))
        stale_tickets = select(Ticket.id).where(Ticket.request_key.like("p14-web-%"))
        stale_users = select(User.id).where(User.login_id.like("p14-login-%"))
        session.execute(delete(Ticket).where(Ticket.id.in_(stale_tickets)))
        session.execute(delete(Inquiry).where(Inquiry.id.in_(stale_inquiries)))
        session.execute(delete(LoginSession).where(LoginSession.user_id.in_(stale_users)))
        session.execute(delete(User).where(User.id.in_(stale_users)))
        session.execute(delete(Employee).where(Employee.name.like("p14-user-%")))
    with create_session_factory(engine).begin() as session:
        employee = Employee(name=employee_name, dept="재무팀")
        session.add(employee)
        session.flush()
        user = User(employee_id=employee.id, login_id=f"p14-login-{suffix}",
            password_hash="unused-fixture-hash", role="employee", is_active=True,
            must_change_password=False)
        session.add(user)
        session.flush()
        user_id = user.id
        employee_id = employee.id
        session.add(LoginSession(user_id=user_id,
            token_hash=hash_session_token(token, session_secret),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))

    settings = Settings(_env_file=None, database_url=SecretStr(os.environ["DATABASE_URL"]),
        session_secret=SecretStr(session_secret), internal_api_key=SecretStr(internal_key),
        n8n_webhook_url="http://n8n.invalid/webhook/oke-support",
        n8n_webhook_key=SecretStr("p1-4-mock-team-key"), backend_origin="http://localhost")

    def fake_client(provided_settings):
        assert provided_settings.n8n_webhook_url == settings.n8n_webhook_url

        async def handler(request):
            payload = json.loads(request.content)
            seen.append((request.headers.get("X-Team-Key"), payload))
            with create_session_factory(engine).begin() as session:
                saved = session.scalar(select(Inquiry).where(Inquiry.request_id == request_id))
                assert saved is not None and saved.status == "submitted"
            return httpx.Response(200, json={
                "request_id": request_id, "route": "담당자 이관", "answer": "접수 안내",
                "sources": [], "ticket": None, "agents": ["triage"],
                "security": {"blocked_by": None, "reason": None, "masked": 0},
                "reason": "urgent", "timings": {"triage": 1.0},
            })

        return SupportClient(provided_settings, transport=httpx.MockTransport(handler))

    monkeypatch.setattr(inquiry_service, "build_support_client", fake_client)
    app = create_app(settings)
    try:
        with TestClient(app) as client:
            client.cookies.set("oke_session", token)
            response = client.post("/api/ask", json={"request_id": request_id,
                "question": "합성 VPN 문의", "attempt": 1})
            assert response.status_code == 200
            assert response.json()["reason"] == "urgent"
            assert seen == [("p1-4-mock-team-key", {
                "request_id": request_id, "user": employee_name,
                "question": "합성 VPN 문의", "channel": "web", "attempt": 1,
            })]
            listed = client.get("/api/my-requests")
            assert listed.status_code == 200
            assert listed.json()["items"][0]["request_id"] == request_id

            ticket = client.post("/tickets", headers={"X-Api-Key": internal_key}, json={
                "key": request_id, "title": "합성 VPN 이관", "requester": employee_name,
                "category": "network", "priority": "high",
            })
            assert ticket.status_code == 201
            with create_session_factory(engine).begin() as session:
                inquiry = session.scalar(select(Inquiry).where(Inquiry.request_id == request_id))
                stored_ticket = session.scalar(select(Ticket).where(
                    Ticket.request_key == request_id))
                assert inquiry is not None and inquiry.status == "completed"
                assert stored_ticket is not None and stored_ticket.inquiry_id == inquiry.id
                assert stored_ticket.ticket_id == ticket.json()["ticket_id"]
    finally:
        with create_session_factory(engine).begin() as session:
            inquiry = session.scalar(select(Inquiry).where(Inquiry.request_id == request_id))
            if inquiry:
                session.execute(delete(Ticket).where(Ticket.inquiry_id == inquiry.id))
                session.execute(delete(Inquiry).where(Inquiry.id == inquiry.id))
            session.execute(delete(LoginSession).where(LoginSession.token_hash ==
                hash_session_token(token, session_secret)))
            session.execute(delete(User).where(User.login_id == f"p14-login-{suffix}"))
            session.execute(delete(Employee).where(Employee.id == employee_id))
        engine.dispose()
