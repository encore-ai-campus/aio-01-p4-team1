"""P1-2 HTTP and ownership checks against the isolated PostgreSQL, with fake C02 HTTP."""

import os
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, func, select

from app.clients.support import SupportClient
from app.core.config import Settings
from app.core.security import hash_session_token, new_session_token
from app.db.models import Employee, Inquiry, Session as LoginSession, User
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from app.services import inquiries as inquiry_service

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires isolated DB opt-in",
)]


def test_00_actual_http_pre_save_c02_mapping_and_user_ownership(monkeypatch):
    engine = create_db_engine()
    suffix = uuid4().hex[:12]
    signing_secret = "p1-2-test-session-signing-secret"
    token_a, token_b = new_session_token(), new_session_token()
    seen = []
    with create_session_factory(engine).begin() as session:
        assert session.scalar(select(func.count()).select_from(Inquiry)) == 0
        employee_a = Employee(name=f"p12-user-a-{suffix}", dept="재무팀")
        employee_b = Employee(name=f"p12-user-b-{suffix}", dept="IT팀")
        session.add_all([employee_a, employee_b])
        session.flush()
        user_a = User(employee_id=employee_a.id, login_id=f"p12-user-a-{suffix}",
            password_hash="unused-fixture-hash", role="employee", is_active=True,
            must_change_password=False)
        user_b = User(employee_id=employee_b.id, login_id=f"p12-user-b-{suffix}",
            password_hash="unused-fixture-hash", role="admin", is_active=True,
            must_change_password=False)
        session.add_all([user_a, user_b])
        session.flush()
        user_a_id, user_b_id = user_a.id, user_b.id
        session.add_all([
            LoginSession(user_id=user_a_id, token_hash=hash_session_token(token_a, signing_secret),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)),
            LoginSession(user_id=user_b_id, token_hash=hash_session_token(token_b, signing_secret),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)),
        ])
        employee_a_id, employee_b_id = employee_a.id, employee_b.id

    settings = Settings(_env_file=None, database_url=SecretStr(os.environ["DATABASE_URL"]),
        session_secret=SecretStr(signing_secret),
        n8n_webhook_url="http://n8n.invalid/webhook/oke-support",
        n8n_webhook_key=SecretStr("fake-c02-team-key"), backend_origin="http://localhost")
    current_outcome = {"status": 200, "payload": None}

    def fake_client(provided_settings):
        assert provided_settings.n8n_webhook_url == settings.n8n_webhook_url

        async def handler(request):
            seen.append(request)
            payload = json.loads(request.content)
            # A separate connection sees the pre-saved inquiry while C02 is running.
            with create_session_factory(engine).begin() as db:
                row = db.scalar(select(Inquiry).where(Inquiry.request_id == payload["request_id"]))
                assert row is not None and row.status == "submitted" and row.result is None
            if current_outcome["payload"] is not None:
                return httpx.Response(current_outcome["status"], json=current_outcome["payload"])
            return httpx.Response(200, json={
                "request_id": payload["request_id"], "route": "자동 답변", "answer": "합성 응답",
                "sources": [], "ticket": None, "agents": ["triage"],
                "security": {"blocked_by": None, "reason": None, "masked": 0},
                "reason": "fixture_reason", "timings": {"triage": 2.0},
                "extra_response": {"preserved": True},
            })

        return SupportClient(provided_settings, transport=httpx.MockTransport(handler))

    monkeypatch.setattr(inquiry_service, "build_support_client", fake_client)
    app = create_app(settings)
    try:
        with TestClient(app) as owner_a, TestClient(app) as owner_b:
            owner_a.cookies.set("oke_session", token_a)
            owner_b.cookies.set("oke_session", token_b)
            response = owner_a.post("/api/ask", json={"request_id": f"p12-{suffix}",
                "question": "VPN 접속 질문", "attempt": 1})
            assert response.status_code == 200
            assert response.json()["extra_response"] == {"preserved": True}
            assert response.json()["reason"] == "fixture_reason"
            assert seen[0].headers["X-Team-Key"] == "fake-c02-team-key"
            assert json.loads(seen[0].content) == {"request_id": f"p12-{suffix}",
                "user": f"p12-user-a-{suffix}", "question": "VPN 접속 질문",
                "channel": "web", "attempt": 1}

            own = owner_a.get("/api/my-requests")
            assert own.status_code == 200 and len(own.json()["items"]) == 1
            assert own.json()["items"][0]["result"]["request_id"] == f"p12-{suffix}"
            assert owner_b.get("/api/my-requests").json()["items"] == []

            before = len(seen)
            wrong_owner = owner_b.post("/api/ask", json={"request_id": f"p12-{suffix}",
                "question": "VPN 접속 질문", "attempt": 1})
            assert wrong_owner.status_code == 403 and len(seen) == before
            changed_payload = owner_a.post("/api/ask", json={"request_id": f"p12-{suffix}",
                "question": "다른 질문", "attempt": 1})
            assert changed_payload.status_code == 409 and len(seen) == before

            generated = owner_a.post("/api/ask", json={"question": "새 ID 발급 질문"})
            assert generated.status_code == 200
            generated_id = generated.json()["request_id"]
            assert generated_id and len(generated_id) <= 64

            invalid = owner_a.post("/api/ask", json={"question": "가" * 501})
            assert invalid.status_code == 400 and len(seen) == before + 1
            assert "가" * 501 not in invalid.text

            current_outcome.update(status=400, payload={"codes": ["question_required"]})
            upstream_400 = owner_a.post("/api/ask", json={"request_id": f"p12-400-{suffix}",
                "question": "유효한 웹 입력"})
            assert upstream_400.status_code == 400
            assert upstream_400.json() == {"codes": ["question_required"]}
            with create_session_factory(engine).begin() as session:
                failed = session.scalar(select(Inquiry).where(
                    Inquiry.request_id == f"p12-400-{suffix}"))
                assert failed is not None and failed.status == "failed" and failed.result is None
    finally:
        with create_session_factory(engine).begin() as session:
            inquiry_ids = select(Inquiry.id).where(Inquiry.requester_id.in_(
                [employee_a_id, employee_b_id]))
            session.execute(delete(Inquiry).where(Inquiry.id.in_(inquiry_ids)))
            session.execute(delete(LoginSession).where(LoginSession.user_id.in_([user_a_id, user_b_id])))
            session.execute(delete(User).where(User.id.in_([user_a_id, user_b_id])))
            session.execute(delete(Employee).where(Employee.id.in_([employee_a_id, employee_b_id])))
        engine.dispose()
