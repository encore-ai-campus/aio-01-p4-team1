"""All successful business behavior in P0-2 lives in test fixtures only."""

import json
from copy import deepcopy
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.deps import get_backend, get_current_user, require_internal_key
from app.api.errors import SupportInputError
from app.core.config import Settings
from app.main import create_app
from app.schemas.auth import UserSummary
from app.schemas.support import SupportRequest, validate_support_response


@pytest.fixture
def support_payload():
    return {
        "request_id": "req-fixture", "route": "자동 답변", "answer": "합성 안내",
        "sources": [{"doc": "remote-work-vpn", "section": "점검", "score": 0.82}],
        "ticket": None, "agents": ["triage", "retriever", "writer", "verifier"],
        "security": {"blocked_by": None, "reason": None, "masked": 0},
    }


@pytest.fixture
def contract_harness(support_payload):
    class MockBackend:
        def __init__(self):
            self.payload = deepcopy(support_payload)
            self.http_status = 200
            self.raw_response = None
            self.calls = []
            self.operations = []
            self.results = {}

        def transport(self, request):
            assert request.headers["X-Team-Key"] == "mock-only"
            self.calls.append(json.loads(request.content))
            if self.raw_response is not None:
                return httpx.Response(self.http_status, content=self.raw_response)
            return httpx.Response(self.http_status, json=self.payload)

        async def execute(self, operation, *, body=None, principal=None, entity_id=None, session_id=None):
            self.operations.append((operation, body, principal, entity_id))
            if operation != "ask":
                if operation not in self.results:
                    raise HTTPException(501)
                return self.results[operation]
            # Test-only contract conversion, not the P1 persistence/client implementation.
            outgoing = SupportRequest(
                request_id=body.request_id or uuid4().hex, user=principal.name,
                question=body.question, attempt=body.attempt, context=body.context,
            )
            async with httpx.AsyncClient(transport=httpx.MockTransport(self.transport)) as client:
                response = await client.post("https://support.invalid/webhook/oke-support",
                                             headers={"X-Team-Key": "mock-only"},
                                             json=outgoing.model_dump(exclude_none=True))
            try:
                payload = response.json()
                if response.status_code == 400 and isinstance(payload.get("codes"), list):
                    raise SupportInputError(payload)
                if response.status_code != 200:
                    raise HTTPException(502)
                return validate_support_response(payload, outgoing.request_id)
            except (ValidationError, ValueError, TypeError, AttributeError):
                raise HTTPException(502) from None

    application = create_app(Settings(_env_file=None))
    backend = MockBackend()
    user = UserSummary(id=1, name="박서연", dept="재무팀", role="employee",
                       must_change_password=False)
    application.dependency_overrides[get_backend] = lambda: backend
    application.dependency_overrides[get_current_user] = lambda: user
    application.dependency_overrides[require_internal_key] = lambda: None
    with TestClient(application, raise_server_exceptions=False) as client:
        yield application, client, backend, user
