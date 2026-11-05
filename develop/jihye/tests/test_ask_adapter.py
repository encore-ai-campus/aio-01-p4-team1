import anyio
import httpx
import json
import pytest

from app.api.errors import PublicApiError, SupportInputError
from app.clients import support
from app.clients.support import SupportClient
from app.core.config import Settings
from app.schemas.support import SupportRequest


def settings():
    return Settings(_env_file=None, n8n_webhook_url="http://n8n.invalid/webhook/oke-support",
                   n8n_webhook_key="mock-team-key")


def response_payload(request_id="req-adapter"):
    return {"request_id": request_id, "route": "자동 답변", "answer": "합성 안내",
            "sources": [{"doc": "mock-doc", "section": "점검", "score": 0.7,
                         "extra_source": "preserved"}],
            "ticket": None, "agents": ["triage", "retriever"],
            "security": {"blocked_by": None, "reason": None, "masked": 0,
                         "extra_security": "preserved"},
            "reason": "fixture_reason", "timings": {"search": 3.25},
            "extra_response": {"kept": True}}


def test_adapter_sends_c02_request_and_preserves_response_extensions():
    seen = []

    async def handler(request):
        seen.append(request)
        return httpx.Response(200, json=response_payload())

    outgoing = SupportRequest(request_id="req-adapter", user="박서연", question="질문",
                              channel="web", attempt=2, context="추가 답변")
    result = anyio.run(SupportClient(settings(), transport=httpx.MockTransport(handler)).ask,
                       outgoing)
    assert result.model_dump(exclude_unset=True)["extra_response"] == {"kept": True}
    assert result.reason == "fixture_reason" and result.timings == {"search": 3.25}
    assert result.sources[0].model_extra["extra_source"] == "preserved"
    assert result.security.model_extra["extra_security"] == "preserved"
    assert len(seen) == 1
    assert seen[0].url == "http://n8n.invalid/webhook/oke-support"
    assert seen[0].headers["X-Team-Key"] == "mock-team-key"
    assert json.loads(seen[0].content) == {"request_id": "req-adapter", "user": "박서연",
        "question": "질문", "channel": "web", "attempt": 2, "context": "추가 답변"}


def test_adapter_passes_through_c02_400_codes_exactly():
    async def handler(request):
        return httpx.Response(400, json={"codes": ["question_required"], "detail": "safe"})

    outgoing = SupportRequest(request_id="req-adapter", user="박서연", question="질문")
    with pytest.raises(SupportInputError) as error:
        anyio.run(SupportClient(settings(), transport=httpx.MockTransport(handler)).ask, outgoing)
    assert error.value.payload == {"codes": ["question_required"], "detail": "safe"}


@pytest.mark.parametrize("status", [401, 403, 404, 500, 503])
def test_adapter_rejects_non_200_outcomes_without_retry(status):
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status, text="private upstream body")

    outgoing = SupportRequest(request_id="req-adapter", user="박서연", question="질문")
    with pytest.raises(PublicApiError) as error:
        anyio.run(SupportClient(settings(), transport=httpx.MockTransport(handler)).ask, outgoing)
    assert error.value.status == 503
    assert calls == 1
    assert "private upstream body" not in str(error.value)


def test_adapter_rejects_wrong_request_id_and_malformed_success():
    outgoing = SupportRequest(request_id="req-adapter", user="박서연", question="질문")

    async def wrong_id(request):
        return httpx.Response(200, json=response_payload("other-id"))

    with pytest.raises(PublicApiError) as mismatch:
        anyio.run(SupportClient(settings(), transport=httpx.MockTransport(wrong_id)).ask,
                  outgoing)
    assert mismatch.value.status == 503

    async def malformed(request):
        return httpx.Response(200, json={"request_id": "req-adapter", "answer": "partial"})

    with pytest.raises(PublicApiError):
        anyio.run(SupportClient(settings(), transport=httpx.MockTransport(malformed)).ask,
                  outgoing)


def test_adapter_applies_connect_and_total_timeout(monkeypatch):
    monkeypatch.setattr(support, "REQUEST_TIMEOUT_SECONDS", 0.01)
    calls = 0

    async def slow(request):
        nonlocal calls
        calls += 1
        await anyio.sleep(0.05)
        return httpx.Response(200, json=response_payload())

    outgoing = SupportRequest(request_id="req-adapter", user="박서연", question="질문")
    with pytest.raises(PublicApiError) as error:
        anyio.run(SupportClient(settings(), transport=httpx.MockTransport(slow)).ask, outgoing)
    assert error.value.status == 504
    assert calls == 1


def test_adapter_fails_closed_when_url_or_key_is_missing():
    outgoing = SupportRequest(request_id="req-adapter", user="박서연", question="질문")
    for config in (Settings(_env_file=None, n8n_webhook_key="key"),
                   Settings(_env_file=None, n8n_webhook_url="http://n8n.invalid/hook")):
        with pytest.raises(PublicApiError) as error:
            anyio.run(SupportClient(config).ask, outgoing)
        assert error.value.status == 503
