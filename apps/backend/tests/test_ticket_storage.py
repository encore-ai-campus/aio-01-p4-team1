"""Unit checks for C05 ACKs, practice transport and internal-key boundaries."""

import json

import anyio
import httpx
import pytest
from pydantic import SecretStr

from app.api.deps import get_backend
from app.api.errors import PublicApiError
from app.clients.practice_store import PracticeStoreClient
from app.core.config import Settings
from app.main import create_app
from app.schemas.alerts import AlertCreate, AlertStoredResponse, DlqCreate
from app.schemas.tickets import TicketCreate
from app.services.alerts import sanitize_safe_payload
from app.services.storage_mode import StorageMode, storage_mode


def test_internal_key_missing_wrong_and_correct_are_distinguished():
    calls = []

    class Backend:
        async def execute(self, operation, **kwargs):
            calls.append(operation)
            return {"ticket_id": "T-2001", "duplicate": False}

    app = create_app(Settings(_env_file=None, internal_api_key=SecretStr("expected-test-key")))
    app.dependency_overrides[get_backend] = lambda: Backend()
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://test") as client:
            payload = {"key": "req-test", "title": "합성", "requester": "박서연",
                       "category": "network", "priority": "normal"}
            assert (await client.post("/tickets", json=payload)).status_code == 401
            assert (await client.post("/tickets", json=payload,
                headers={"X-Api-Key": "wrong-test-key"})).status_code == 401
            response = await client.post("/tickets", json=payload,
                headers={"X-Api-Key": "expected-test-key"})
            assert response.status_code == 201
            assert response.json() == {"ticket_id": "T-2001", "duplicate": False}
    anyio.run(exercise)
    assert calls == ["create_ticket"]


def test_internal_key_configuration_missing_fails_closed():
    app = create_app(Settings(_env_file=None, internal_api_key=None))
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://test") as client:
            return await client.post("/tickets", json={}, headers={"X-Api-Key": "provided-test-key"})
    response = anyio.run(exercise)
    assert response.status_code == 503
    assert "provided-test-key" not in response.text


@pytest.mark.parametrize("event_key,expected", [
    (None, {"workflow": "oke-handoff", "node": "ticket", "message": "ok", "severity": "high"}),
    ("evt-one", {"workflow": "oke-handoff", "node": "ticket", "message": "ok", "severity": "high", "event_key": "evt-one"}),
])
def test_practice_alert_ack_legacy_and_explicit_duplicate(event_key, expected):
    response_body = {"stored": 1, "count": 5} if event_key is None else {
        "stored": 0, "count": 5, "duplicate": True}
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=response_body)

    settings = Settings(_env_file=None, service_mode="practice", data_api_url="http://data-api:8800",
                        data_api_key=SecretStr("practice-test-key"))
    client = PracticeStoreClient(settings, transport=httpx.MockTransport(handler))
    payload = AlertCreate(workflow="oke-handoff", node="ticket", message="ok", severity="high",
                          event_key=event_key)
    ack = client.create_alert(payload)
    assert ack.model_dump() == {"stored": response_body["stored"], "count": 5,
                                "duplicate": event_key is not None}
    assert seen[0].url.path == "/alerts"
    assert seen[0].headers["X-Api-Key"] == "practice-test-key"
    assert json.loads(seen[0].content) == expected


def test_practice_alert_rejects_count_only_as_duplicate_proof():
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"stored": 0, "count": 7}))
    settings = Settings(_env_file=None, service_mode="practice", data_api_url="http://data-api:8800",
                        data_api_key=SecretStr("practice-test-key"))
    client = PracticeStoreClient(settings, transport=transport)
    with pytest.raises(PublicApiError) as error:
        client.create_alert(AlertCreate(workflow="w", node="n", message="m", severity="high", event_key="e"))
    assert error.value.status == 503


def test_practice_ticket_requires_status_duplicate_pair():
    settings = Settings(_env_file=None, service_mode="practice", data_api_url="http://data-api:8800",
                        data_api_key=SecretStr("practice-test-key"))
    duplicate = PracticeStoreClient(settings, transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json={"ticket_id": "T-2001", "duplicate": True})))
    assert duplicate.create_ticket(TicketCreate(key="req-test", title="t", requester="박서연",
        category="network", priority="normal")).duplicate is True

    invalid = PracticeStoreClient(settings, transport=httpx.MockTransport(
        lambda _: httpx.Response(201, json={"ticket_id": "T-2001", "duplicate": True})))
    with pytest.raises(PublicApiError):
        invalid.create_ticket(TicketCreate(key="req-test", title="t", requester="박서연",
            category="network", priority="normal"))


def test_practice_dlq_keeps_required_nullable_request_id():
    seen = []
    settings = Settings(_env_file=None, service_mode="practice", data_api_url="http://data-api:8800",
                        data_api_key=SecretStr("practice-test-key"))
    client = PracticeStoreClient(settings, transport=httpx.MockTransport(
        lambda request: (seen.append(request) or httpx.Response(200, json={"stored": 1, "count": 9}))))
    ack = client.create_dlq(DlqCreate(request_id=None, workflow="w", node="n", reason="failed",
                                      safe_payload={"stage": "ticket"}))
    assert ack.model_dump() == {"stored": 1, "count": 9}
    assert json.loads(seen[0].content)["request_id"] is None


def test_dlq_payload_sanitizes_secret_and_contact_values():
    payload = sanitize_safe_payload({"stage": "alert", "api_key": "secret-value",
        "detail": "contact person@example.test or 010-1234-5678; Bearer abc.def"})
    serialized = json.dumps(payload)
    assert "secret-value" not in serialized
    assert "person@example.test" not in serialized
    assert "010-1234-5678" not in serialized
    assert "abc.def" not in serialized
    assert payload["api_key"] == "[REDACTED]"


@pytest.mark.parametrize("mode,expected", [("app", StorageMode.APP), ("practice", StorageMode.PRACTICE)])
def test_storage_mode_selection(mode, expected):
    assert storage_mode(Settings(_env_file=None, service_mode=mode)) is expected
