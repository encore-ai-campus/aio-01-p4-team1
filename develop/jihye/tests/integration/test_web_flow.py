"""Exercise browser inquiry persistence and C05 ticket linkage on isolated PostgreSQL."""

import json
import os
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, or_, select, update

from app.clients.support import SupportClient
from app.core.config import Settings
from app.core.security import hash_password
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
    session_secret = "p1-4-local-session-fixture"
    internal_key = "p1-4-local-internal-fixture"
    user_password = "Fixture-User-746!"
    admin_password = "Fixture-Admin-746!"
    seen = []
    stored_ticket_id = None
    # Remove only stale fixtures from this test after an interrupted prior run.
    with create_session_factory(engine).begin() as session:
        stale_inquiries = select(Inquiry.id).where(Inquiry.request_id.like("p14-web-%"))
        stale_tickets = select(Ticket.id).where(Ticket.request_key.like("p14-web-%"))
        stale_users = select(User.id).where(or_(User.login_id.like("p14-login-%"),
                                                User.login_id.like("p14-admin-login-%")))
        stale_employees = select(Employee.id).where(or_(Employee.name.like("p14-user-%"),
                                                        Employee.name.like("p14-admin-%")))
        session.execute(delete(Ticket).where(Ticket.id.in_(stale_tickets)))
        session.execute(delete(Inquiry).where(Inquiry.id.in_(stale_inquiries)))
        session.execute(delete(LoginSession).where(LoginSession.user_id.in_(stale_users)))
        session.execute(delete(User).where(User.id.in_(stale_users)))
        session.execute(delete(Employee).where(Employee.id.in_(stale_employees)))
    with create_session_factory(engine).begin() as session:
        employee = Employee(name=employee_name, dept="재무팀")
        admin_employee = Employee(name=f"p14-admin-{suffix}", dept="IT팀")
        session.add_all([employee, admin_employee])
        session.flush()
        user = User(employee_id=employee.id, login_id=f"p14-login-{suffix}",
            password_hash=hash_password(user_password), role="employee", is_active=True,
            must_change_password=False)
        admin_user = User(employee_id=admin_employee.id, login_id=f"p14-admin-login-{suffix}",
            password_hash=hash_password(admin_password), role="admin", is_active=True,
            must_change_password=False)
        session.add_all([user, admin_user])
        session.flush()
        user_id = user.id
        admin_user_id = admin_user.id
        employee_id = employee.id
        admin_employee_id = admin_employee.id

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
        with TestClient(app) as client, TestClient(app) as admin_client:
            login = client.post("/api/auth/login", json={
                "login_id": f"p14-login-{suffix}", "password": user_password})
            assert login.status_code == 200
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
                stored_ticket_id = stored_ticket.id

            admin_login = admin_client.post("/api/auth/login", json={
                "login_id": f"p14-admin-login-{suffix}", "password": admin_password})
            assert admin_login.status_code == 200
            admin_listed = admin_client.get("/api/admin/tickets")
            assert admin_listed.status_code == 200
            admin_ticket = next(row for row in admin_listed.json()["items"]
                                if row["id"] == stored_ticket_id)
            assert admin_ticket["question"] == "합성 VPN 문의"
            patched = admin_client.patch(f"/api/admin/tickets/{stored_ticket_id}", json={
                "status": "resolved", "reply": "담당자가 확인했습니다."})
            assert patched.status_code == 200
            assert patched.json()["question"] == "합성 VPN 문의"

            # A fresh session reads current app.tickets state; saved C02 result stays immutable.
            assert client.post("/api/auth/logout").status_code == 200
            relogin = client.post("/api/auth/login", json={
                "login_id": f"p14-login-{suffix}", "password": user_password})
            assert relogin.status_code == 200
            listed = client.get("/api/my-requests")
            assert listed.status_code == 200
            item = next(row for row in listed.json()["items"] if row["request_id"] == request_id)
            assert item["ticket"]["ticket_id"] == ticket.json()["ticket_id"]
            assert item["ticket"]["status"] == "resolved"
            assert item["ticket"]["reply"] == "담당자가 확인했습니다."
            assert item["result"]["ticket"] is None

            # A mismatched ticket relation must never disclose its ID or reply to this employee.
            with create_session_factory(engine).begin() as session:
                session.execute(update(Ticket).where(Ticket.id == stored_ticket_id)
                                .values(requester_id=admin_employee_id))
            assert client.get("/api/my-requests").json()["items"][0]["ticket"] is None
            with create_session_factory(engine).begin() as session:
                session.execute(update(Ticket).where(Ticket.id == stored_ticket_id)
                                .values(requester_id=employee_id,
                                        request_key=f"p14-unrelated-{suffix}"))
            assert client.get("/api/my-requests").json()["items"][0]["ticket"] is None
            with create_session_factory(engine).begin() as session:
                session.execute(update(Ticket).where(Ticket.id == stored_ticket_id)
                                .values(request_key=request_id, inquiry_id=None))
            admin_ticket_without_fk = next(
                row for row in admin_client.get("/api/admin/tickets").json()["items"]
                if row["id"] == stored_ticket_id)
            assert admin_ticket_without_fk["question"] == "합성 VPN 문의"
            assert client.get("/api/my-requests").json()["items"][0]["ticket"] is None
    finally:
        with create_session_factory(engine).begin() as session:
            inquiry = session.scalar(select(Inquiry).where(Inquiry.request_id == request_id))
            if inquiry:
                session.execute(delete(Ticket).where(or_(Ticket.id == stored_ticket_id,
                                                        Ticket.inquiry_id == inquiry.id)))
                session.execute(delete(Inquiry).where(Inquiry.id == inquiry.id))
            session.execute(delete(LoginSession).where(LoginSession.user_id.in_(
                [user_id, admin_user_id])))
            session.execute(delete(User).where(User.id.in_([user_id, admin_user_id])))
            session.execute(delete(Employee).where(Employee.id.in_(
                [employee_id, admin_employee_id])))
        engine.dispose()
