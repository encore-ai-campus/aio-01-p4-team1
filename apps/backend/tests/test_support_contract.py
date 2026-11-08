from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.support import AskRequest, SupportRequest, SupportResponse, validate_support_response


@pytest.mark.parametrize("route", ["자동 답변", "보완 질문", "담당자 이관", "권한 없음", "차단"])
def test_routes_preserve_response(contract_harness, route):
    _, client, backend, _ = contract_harness
    backend.payload.update(route=route, reason="fixture", timings={"total": 10.5},
                           extension={"kept": True})
    backend.payload["security"]["new_field"] = "kept"
    backend.payload["sources"][0]["source_extra"] = "kept"
    if route == "담당자 이관":
        backend.payload["ticket"] = {"ticket_id": "T-2001", "priority": "normal", "duplicate": False}
    response = client.post("/api/ask", json={"question": "문의", "request_id": "req-fixture"})
    assert response.status_code == 200
    assert response.json() == backend.payload


def test_web_identity_is_not_taken_from_input(contract_harness):
    _, client, backend, _ = contract_harness
    response = client.post("/api/ask", json={
        "question": "문의", "request_id": "req-fixture", "user": "김민지",
        "role": "admin", "dept": "IT팀", "channel": "injected",
    })
    assert response.status_code == 200
    assert backend.calls == [{"request_id": "req-fixture", "user": "박서연", "question": "문의",
                              "channel": "web", "attempt": 1}]


def test_400_codes_passthrough(contract_harness):
    _, client, backend, _ = contract_harness
    backend.http_status = 400
    backend.payload = {"codes": ["question_required"], "message": "합성 오류", "extra": "preserved"}
    response = client.post("/api/ask", json={"question": "문의", "request_id": "req-fixture"})
    assert response.status_code == 400
    assert response.json() == backend.payload


@pytest.mark.parametrize("mutation", [
    {"request_id": "other"}, {"route": "invalid"}, {"answer": 123},
    {"sources": [{"doc": "d", "section": "s", "score": "0.8"}]},
    {"security": {"masked": -1, "reason": None, "blocked_by": None}},
    {"ticket": {"ticket_id": "T-2001", "priority": "urgent", "duplicate": False}},
    {"agents": "writer"}, {"timings": {"total": -1}},
])
def test_invalid_upstream_is_not_success(contract_harness, mutation):
    _, client, backend, _ = contract_harness
    backend.payload.update(mutation)
    response = client.post("/api/ask", json={"question": "문의", "request_id": "req-fixture"})
    assert response.status_code == 502


@pytest.mark.parametrize("field", ["request_id", "route", "answer", "sources", "ticket", "agents", "security"])
def test_required_response_fields(support_payload, field):
    payload = deepcopy(support_payload)
    del payload[field]
    with pytest.raises(ValidationError):
        SupportResponse.model_validate(payload)


def test_no_optional_fields_added(contract_harness):
    _, client, backend, _ = contract_harness
    response = client.post("/api/ask", json={"question": "문의", "request_id": "req-fixture"})
    assert response.json() == backend.payload


def test_invalid_json_and_nonfinite_score(contract_harness, support_payload):
    _, client, backend, _ = contract_harness
    backend.raw_response = b"not-json"
    assert client.post("/api/ask", json={"question": "문의"}).status_code == 502
    for value in [float("nan"), float("inf"), float("-inf")]:
        payload = deepcopy(support_payload)
        payload["sources"][0]["score"] = value
        with pytest.raises(ValidationError):
            validate_support_response(payload, "req-fixture")


@pytest.mark.parametrize("payload", [{"question": " "}, {"question": "가" * 501},
                                      {"question": "문의", "attempt": True},
                                      {"question": "문의", "request_id": "x" * 65}])
def test_invalid_ask_never_calls_transport(contract_harness, payload):
    _, client, backend, _ = contract_harness
    assert client.post("/api/ask", json=payload).status_code == 400
    assert backend.calls == []
    assert backend.operations == []


@pytest.mark.parametrize("model", [AskRequest, SupportRequest])
@pytest.mark.parametrize("context", ["", "가" * 2000, " " * 2000, None])
def test_context_accepted_boundaries(model, context):
    kwargs = {"question": "문의", "request_id": "req-fixture", "context": context}
    if model is SupportRequest:
        kwargs["user"] = "박서연"
    result = model.model_validate(kwargs)
    assert result.context == context  # no trim or silent truncation
    del kwargs["context"]
    assert model.model_validate(kwargs).context is None


@pytest.mark.parametrize("model", [AskRequest, SupportRequest])
@pytest.mark.parametrize("context", ["가" * 2001, 1, True, ["text"], {"text": "문의"}])
def test_context_invalid_length_and_types(model, context):
    kwargs = {"question": "문의", "request_id": "req-fixture", "context": context}
    if model is SupportRequest:
        kwargs["user"] = "박서연"
    with pytest.raises(ValidationError):
        model.model_validate(kwargs)


def test_context_at_limit_reaches_mock_unchanged(contract_harness):
    _, client, backend, _ = contract_harness
    context = "가" * 2000
    response = client.post("/api/ask", json={
        "question": "문의", "request_id": "req-fixture", "context": context,
    })
    assert response.status_code == 200
    assert backend.calls[0]["context"] == context


@pytest.mark.parametrize("context", ["가" * 2001, 1, True, ["text"], {"text": "문의"}])
def test_invalid_context_returns_safe_400_without_call(contract_harness, context):
    _, client, backend, _ = contract_harness
    response = client.post("/api/ask", json={"question": "문의", "context": context})
    assert response.status_code == 400
    assert response.json() == {
        "error": {"code": "invalid_input", "message": "입력값을 확인해 주세요."},
    }
    assert backend.calls == []
    assert backend.operations == []


def test_context_limit_is_in_openapi(contract_harness):
    application, _, _, _ = contract_harness
    schemas = application.openapi()["components"]["schemas"]
    for schema in (schemas["AskRequest"], SupportRequest.model_json_schema()):
        variants = schema["properties"]["context"]["anyOf"]
        assert {"type": "string", "maxLength": 2000} in variants
