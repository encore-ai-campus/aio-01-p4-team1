from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.support import SupportResponse, validate_support_response


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
