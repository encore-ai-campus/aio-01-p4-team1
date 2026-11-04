import secrets

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.main import create_app
from app.schemas.common import Attempt, Question, RequestId


class ContractProbe(BaseModel):
    question: Question
    request_id: RequestId
    attempt: Attempt = 1


@pytest.fixture
def client():
    application = create_app(Settings(_env_file=None))

    # Test-only routes exercise the installed handlers without publishing ask/auth.
    @application.post("/_probe")
    def probe(body: ContractProbe) -> ContractProbe:
        return body

    @application.get("/_error/{status}")
    def fail(status: int):
        raise HTTPException(status, detail=secrets.token_urlsafe(24))

    @application.get("/_crash")
    def crash():
        raise RuntimeError(secrets.token_urlsafe(24))

    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.parametrize("field,value", [
    ("question", ""), ("question", " \t\n"), ("question", "가" * 501),
    ("question", 123), ("question", True),
    ("request_id", ""), ("request_id", " " * 4), ("request_id", "r" * 65),
    ("request_id", 123),
    ("attempt", 0), ("attempt", -1), ("attempt", "1"),
    ("attempt", True), ("attempt", False), ("attempt", 1.0), ("attempt", None),
])
def test_invalid_boundaries_return_safe_400(client, field, value):
    payload = {"question": "VPN 문의", "request_id": "req-001", "attempt": 1}
    payload[field] = value
    response = client.post("/_probe", json=payload)
    assert response.status_code == 400
    assert response.json() == {
        "error": {"code": "invalid_input", "message": "입력값을 확인해 주세요."}
    }


def test_valid_boundaries_and_question_trimming(client):
    response = client.post("/_probe", json={
        "question": " \n" + "가" * 500 + "\t ", "request_id": "r" * 64, "attempt": 1,
    })
    assert response.status_code == 200
    assert response.json() == {
        "question": "가" * 500, "request_id": "r" * 64, "attempt": 1,
    }
    assert ContractProbe(question="문의", request_id="req").attempt == 1


def test_validation_errors_do_not_echo_input(client):
    private_input = secrets.token_urlsafe(24)
    for response in (
        client.post("/_probe", json={"question": private_input, "attempt": private_input}),
        client.post("/_probe", content='{"password":"' + private_input + '"',
                    headers={"Content-Type": "application/json"}),
    ):
        assert response.status_code == 400
        assert private_input not in response.text
        assert set(response.json()) == {"error"}


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409])
def test_http_errors_use_web_envelope(client, status):
    response = client.get(f"/_error/{status}")
    assert response.status_code == status
    assert set(response.json()["error"]) == {"code", "message"}
    assert "detail" not in response.json()


def test_server_error_is_safe(client):
    response = client.get("/_crash")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"


def test_liveness_and_only_health_is_published():
    application = create_app(Settings(_env_file=None))
    with TestClient(application) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").status_code == 404
        assert client.post("/api/auth/signup").status_code == 404
        assert client.get("/health/live").status_code == 200
    assert set(application.openapi()["paths"]) == {"/health/live"}


@pytest.mark.parametrize("mode", ["practice", "app"])
def test_service_modes_from_environment(monkeypatch, mode):
    monkeypatch.setenv("SERVICE_MODE", mode)
    assert Settings(_env_file=None).service_mode == mode


def test_invalid_mode_fails_without_echo(monkeypatch):
    private_input = secrets.token_urlsafe(24)
    monkeypatch.setenv("SERVICE_MODE", private_input)
    with pytest.raises(ValidationError) as caught:
        create_app()
    assert private_input not in str(caught.value)


def test_common_environment_and_secret_serialization(monkeypatch):
    private_input = secrets.token_urlsafe(24)
    secret_names = ["DATABASE_URL", "N8N_WEBHOOK_KEY", "INTERNAL_API_KEY",
                    "DATA_API_KEY", "SESSION_SECRET", "BOOTSTRAP_ADMIN_PASSWORD"]
    for name in secret_names:
        monkeypatch.setenv(name, private_input)
    for name in ["N8N_WEBHOOK_URL", "DATA_API_URL", "BACKEND_ORIGIN"]:
        monkeypatch.setenv(name, "http://127.0.0.1:8000")
    settings = Settings(_env_file=None)
    for name in secret_names:
        assert getattr(settings, name.lower()).get_secret_value() == private_input
        assert name not in settings.model_dump()
        assert name.lower() not in settings.model_dump(by_alias=False)
    assert private_input not in repr(settings)
    assert private_input not in str(settings)
    assert private_input not in settings.model_dump_json()
    assert str(settings.backend_origin) == "http://127.0.0.1:8000/"


def test_invalid_url_is_rejected(monkeypatch):
    monkeypatch.setenv("DATA_API_URL", "invalid-url")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
