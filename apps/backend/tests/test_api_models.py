import secrets
from datetime import datetime, timezone

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.deps import get_current_user
from app.core.config import Settings
from app.main import create_app
from app.schemas.auth import ChangePasswordRequest, LoginRequest, UserSummary
from app.schemas.support import AskRequest
from app.schemas.tickets import TicketPatch
from app.schemas.users import CreateUserRequest, ResetPasswordRequest, UserActivePatch

WEB = {
    "/api/auth/login": {"post"}, "/api/auth/logout": {"post"}, "/api/auth/me": {"get"},
    "/api/auth/change-password": {"post"}, "/api/ask": {"post"}, "/api/my-requests": {"get"},
    "/api/admin/tickets": {"get"}, "/api/admin/tickets/{id}": {"patch"},
    "/api/admin/employees": {"get", "post"}, "/api/admin/users": {"get", "post"},
    "/api/admin/users/{id}": {"patch", "delete"},
    "/api/admin/users/{id}/reset-password": {"post"},
    "/api/admin/alerts": {"get"},
}


def test_openapi_matches_current_contract():
    schema = create_app().openapi()
    paths = schema["paths"]
    assert {p: set(ops) for p, ops in paths.items() if p.startswith("/api/")} == WEB
    assert sum(len(ops) for ops in WEB.values()) == 16
    assert set(paths) == set(WEB) | {"/health/live", "/health/ready", "/tickets", "/alerts", "/dlq"}
    for path, operations in paths.items():
        for method, operation in operations.items():
            if not path.startswith("/health/"):
                assert "400" in operation["responses"]
                assert "501" in operation["responses"]
                assert "422" not in operation["responses"]
                if method in {"post", "patch"} and path != "/api/auth/logout":
                    assert operation["requestBody"]["required"]
    schemes = schema["components"]["securitySchemes"]
    assert schemes["APIKeyCookie"]["name"] == "oke_session"
    assert schemes["APIKeyHeader"]["name"] == "X-Api-Key"
    assert paths["/api/ask"]["post"]["security"] == [{"APIKeyCookie": []}]
    for path in ["/tickets", "/alerts", "/dlq"]:
        assert paths[path]["post"]["security"] == [{"APIKeyHeader": []}]
    assert {"200", "201"} <= paths["/tickets"]["post"]["responses"].keys()
    assert paths["/api/admin/users"]["post"]["responses"]["201"]
    assert "anyOf" in paths["/api/ask"]["post"]["responses"]["400"]["content"]["application/json"]["schema"]
    assert schema["components"]["schemas"]["LoginRequest"]["properties"]["password"]["writeOnly"]
    assert "duplicate" in schema["components"]["schemas"]["AlertStoredResponse"]["properties"]


def test_unimplemented_endpoints_do_not_claim_success():
    with TestClient(create_app(Settings(_env_file=None, database_url=None,
                                       session_secret=secrets.token_urlsafe(24)))) as client:
        response = client.post("/api/auth/login", json={
            "login_id": "fixture", "password": secrets.token_urlsafe(20),
        })
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "service_unavailable"
        assert "set-cookie" not in response.headers
        assert client.get("/api/auth/me").status_code == 401
        client.cookies.set("oke_session", secrets.token_urlsafe(20))
        assert client.get("/api/auth/me").status_code == 503
        assert client.post("/tickets", json={}).status_code == 503
        assert client.post("/tickets", json={}, headers={"X-Api-Key": secrets.token_urlsafe(20)}).status_code == 503


def test_password_models_do_not_serialize_plaintext():
    password = secrets.token_urlsafe(20) + "aA1!"
    models = [LoginRequest(login_id="fixture", password=password),
              ChangePasswordRequest(current_password=password, new_password=password),
              CreateUserRequest(employee_id=1, login_id="fixture", temporary_password=password),
              ResetPasswordRequest(temporary_password=password)]
    for model in models:
        assert password not in repr(model)
        assert password not in str(model.model_dump())
        assert password not in model.model_dump_json()
    assert models[0].password.get_secret_value() == password


@pytest.mark.parametrize("password", ["aA1!", "abcdefghijklmnop", "ABCDEFGHIJKLMNOP", "123456789012"])
def test_new_password_shape(password):
    with pytest.raises(ValidationError):
        ResetPasswordRequest(temporary_password=password)


@pytest.mark.parametrize("value", ["false", 0, 1, None])
def test_active_flag_strict(value):
    with pytest.raises(ValidationError):
        UserActivePatch(is_active=value)


def test_patch_omission_and_null_are_distinct():
    assert TicketPatch(status="open").model_dump(exclude_unset=True) == {"status": "open"}
    assert TicketPatch(status="open", assignee=None).model_dump(exclude_unset=True) == {
        "status": "open", "assignee": None,
    }
    with pytest.raises(ValidationError):
        TicketPatch(status="접수")
    for assignee in [True, "5", 0]:
        with pytest.raises(ValidationError):
            TicketPatch(status="open", assignee=assignee)


def test_unknown_identity_is_ignored():
    body = AskRequest.model_validate({"question": "문의", "user": "김민지", "role": "admin"})
    assert not hasattr(body, "user")
    assert not hasattr(body, "role")


def test_admin_guard_and_password_change_boundary(contract_harness):
    _, client, backend, user = contract_harness
    assert client.get("/api/admin/users").status_code == 403
    assert backend.operations == []
    user.must_change_password = True
    assert client.get("/api/auth/me").status_code == 200
    response = client.post("/api/ask", json={"question": "문의"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "password_change_required"
    assert backend.operations == []
    user.must_change_password = False
    user.role = "admin"
    assert client.get("/api/admin/users").status_code == 403  # non-IT admin rejected


def test_all_route_signatures_with_fixture_services(contract_harness):
    application, client, backend, user = contract_harness
    admin = UserSummary(id=2, name="김민지", dept="IT팀", role="admin", must_change_password=False)
    def authenticated_admin(request: Request):
        request.state.auth_session_id = 27
        return admin

    application.dependency_overrides[get_current_user] = authenticated_admin
    now = datetime.now(timezone.utc)
    password = secrets.token_urlsafe(20) + "aA1!"
    account = {**admin.model_dump(), "employee_id": 5, "login_id": "fixture", "is_active": True,
               "password_hash": secrets.token_urlsafe(20), "token_hash": secrets.token_urlsafe(20)}
    ticket = {"id": 1, "ticket_id": "T-2001", "request_id": "req-fixture", "requester": user.name,
              "title": "합성 문의", "category": "network", "priority": "normal", "status": "open",
              "assignee": None, "reply": None, "question": "원문 질문", "created_at": now,
              "updated_at": now}
    backend.results.update(
        login={"user": account, "_token": "fixture-only-token"}, logout={"ok": True},
        change_password={"ok": True, "must_change_password": False},
        employees={"items": [{"id": 5, "name": admin.name, "dept": admin.dept, "user_id": 2}]},
        create_employee={"id": 6, "name": "신규 직원", "dept": "영업팀", "user_id": None},
        users={"items": [account]}, create_user=account, update_user=account,
        delete_user={"ok": True, "message": "계정이 삭제되었습니다."},
        reset_password={"ok": True, "must_change_password": True},
        my_requests={"items": [{"request_id": "req-fixture", "question": "문의", "attempt": 1,
                                "result": None, "ticket": None, "created_at": now}]},
        tickets={"items": [ticket]}, update_ticket=ticket,
        alerts={"items": [{"id": 1, "ticket_id": None, "workflow": "fixture", "node": "fixture",
                           "message": "합성 안내", "severity": "high", "created_at": now}]},
        create_ticket={"ticket_id": "T-2001", "duplicate": False},
        create_alert={"stored": 1, "count": 1, "duplicate": False}, create_dlq={"stored": 1, "count": 1},
    )
    cases = [
        ("post", "/api/auth/login", {"login_id": "fixture", "password": password}, 200),
        ("post", "/api/auth/logout", None, 200), ("get", "/api/auth/me", None, 200),
        ("post", "/api/auth/change-password", {"current_password": password, "new_password": password}, 200),
        ("post", "/api/ask", {"question": "문의", "request_id": "req-fixture"}, 200),
        ("get", "/api/my-requests", None, 200), ("get", "/api/admin/tickets", None, 200),
        ("patch", "/api/admin/tickets/1", {"status": "in_progress", "assignee": 5}, 200),
        ("get", "/api/admin/employees", None, 200),
        ("post", "/api/admin/employees", {"name": "신규 직원", "dept": "영업팀"}, 201),
        ("get", "/api/admin/users", None, 200),
        ("post", "/api/admin/users", {"employee_id": 5, "login_id": "fixture", "temporary_password": password}, 201),
        ("patch", "/api/admin/users/2", {"is_active": False}, 200),
        ("delete", "/api/admin/users/3", None, 200),
        ("post", "/api/admin/users/2/reset-password", {"temporary_password": password}, 200),
        ("get", "/api/admin/alerts", None, 200),
        ("post", "/tickets", {"key": "req-fixture", "title": "문의", "requester": user.name,
                                "category": "network", "priority": "normal"}, 201),
        ("post", "/alerts", {"workflow": "fixture", "node": "fixture", "message": "안내",
                               "severity": "high", "event_key": "evt-fixture"}, 200),
        ("post", "/dlq", {"request_id": None, "workflow": "fixture", "node": "fixture",
                            "reason": "fixture", "safe_payload": {}}, 200),
    ]
    for method, path, body, expected in cases:
        response = client.request(method, path, json=body) if body is not None else client.request(method, path)
        assert response.status_code == expected, (path, response.text)
        if path == "/api/admin/tickets":
            assert response.json()["items"][0]["question"] == "원문 질문"
        elif path == "/api/admin/tickets/1":
            assert response.json()["question"] == "원문 질문"
        elif path == "/api/admin/employees" and method == "post":
            assert response.json() == {"id": 6, "name": "신규 직원", "dept": "영업팀",
                                       "user_id": None}
        elif path == "/api/admin/users/3" and method == "delete":
            assert response.json() == {"ok": True, "message": "계정이 삭제되었습니다."}
        for secret in [password, account["password_hash"], account["token_hash"]]:
            assert secret not in response.text
        if path == "/api/auth/login":
            assert "oke_session=" in response.headers.get("set-cookie", "")
            assert "fixture-only-token" not in response.text


def test_ticket_ack_controls_new_and_duplicate_http_status(contract_harness):
    _, client, backend, _ = contract_harness
    payload = {"key": "req-fixture", "title": "문의", "requester": "박서연",
               "category": "network", "priority": "normal"}
    backend.results["create_ticket"] = {"ticket_id": "T-2001", "duplicate": False}
    first = client.post("/tickets", json=payload, headers={"X-Api-Key": "mock-only"})
    assert first.status_code == 201
    backend.results["create_ticket"] = {"ticket_id": "T-2001", "duplicate": True}
    again = client.post("/tickets", json=payload, headers={"X-Api-Key": "mock-only"})
    assert again.status_code == 200


def test_password_validation_errors_are_safe(contract_harness):
    _, client, _, _ = contract_harness
    private_input = secrets.token_urlsafe(20)
    response = client.post("/api/auth/login", json={"password": private_input})
    assert response.status_code == 400
    assert private_input not in response.text


def test_duplicate_ticket_status_from_fixture(contract_harness):
    _, client, backend, user = contract_harness
    backend.results["create_ticket"] = {"ticket_id": "T-2001", "duplicate": True}
    response = client.post("/tickets", json={"key": "req-fixture", "title": "문의",
        "requester": user.name, "category": "network", "priority": "normal"})
    assert response.status_code == 200
    assert response.json() == backend.results["create_ticket"]
