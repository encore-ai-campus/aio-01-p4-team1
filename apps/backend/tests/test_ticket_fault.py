"""Fault scope, expiry and the existing internal authentication boundary."""

import json

import anyio
import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.ticket_fault import ticket_fault_active
from app.main import create_app

RID = "audit-fault-" + "a" * 32


def arm(path, **updates):
    rule = {"request_id": RID, "armed_at": 1000, "expires_at": 1300, **updates}
    path.write_text(json.dumps(rule))


def test_switch_only_matches_selected_id_during_bounded_window(tmp_path, monkeypatch):
    path = tmp_path / "active.json"
    monkeypatch.setattr("app.core.ticket_fault.time.time", lambda: 1000)
    assert not ticket_fault_active(path, RID)
    arm(path)
    assert ticket_fault_active(path, RID)
    assert not ticket_fault_active(path, "audit-fault-" + "b" * 32)
    assert not ticket_fault_active(path, "ordinary-request")
    monkeypatch.setattr("app.core.ticket_fault.time.time", lambda: 1300)
    assert not ticket_fault_active(path, RID)
    path.unlink()
    assert not ticket_fault_active(path, RID)


@pytest.mark.parametrize("updates", [
    {"armed_at": 1100}, {"expires_at": 1301}, {"expires_at": 1000},
    {"expires_at": "1300"}, {"armed_at": True}, {"expires_at": float("nan")},
    {"expires_at": float("inf")}, {"request_id": "ordinary-request"},
])
def test_invalid_rules_never_disable_ticket_writes(tmp_path, monkeypatch, updates):
    path = tmp_path / "active.json"
    monkeypatch.setattr("app.core.ticket_fault.time.time", lambda: 1000)
    arm(path, **updates)
    assert not ticket_fault_active(path, RID)


@pytest.mark.parametrize("content", ["{", "[]", "null", "x" * 1025, "\ud800"])
def test_unreadable_rules_leave_writes_intact(tmp_path, content):
    path = tmp_path / "active.json"
    path.write_bytes(content.encode("utf-8", errors="surrogatepass"))
    assert not ticket_fault_active(path, RID)


def test_fault_requires_internal_auth_and_does_not_touch_database(tmp_path, monkeypatch):
    path = tmp_path / "active.json"
    arm(path)
    monkeypatch.setattr("app.core.ticket_fault.time.time", lambda: 1000)
    app = create_app(Settings(_env_file=None, ticket_fault_file=path,
        internal_api_key=SecretStr("internal-test-key")))
    payload = {"key": RID, "title": "시험", "requester": "한지훈",
               "category": "other", "priority": "normal"}

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://test") as client:
            assert (await client.post("/tickets", json=payload)).status_code == 401
            assert (await client.post("/tickets", json=payload,
                headers={"X-Api-Key": "wrong"})).status_code == 401
            response = await client.post("/tickets", json=payload,
                headers={"X-Api-Key": "internal-test-key"})
            assert response.status_code == 503
            assert response.json()["error"]["code"] == "service_unavailable"
            # No DB is configured: selected fault ran before any database connection.
            assert "active.json" not in response.text
            assert RID not in response.text
    anyio.run(exercise)
