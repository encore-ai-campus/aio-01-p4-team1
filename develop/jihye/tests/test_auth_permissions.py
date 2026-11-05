from fastapi import Request
from fastapi.testclient import TestClient

from app.api.deps import get_backend, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.schemas.auth import UserSummary


class AuthBackend:
    async def execute(self, operation, *, body=None, principal=None, entity_id=None, session_id=None):
        if operation == "login":
            return {"user": {"id": 7, "name": "박서연", "dept": "재무팀",
                             "role": "employee", "must_change_password": True},
                    "_token": "opaque-fixture-token"}
        if operation == "logout":
            assert session_id == 19
            return {"ok": True}
        raise AssertionError(f"unexpected operation: {operation}")


def test_login_sets_opaque_http_only_cookie_and_never_returns_token():
    app = create_app(Settings(_env_file=None, backend_origin="https://backend.invalid"))
    app.dependency_overrides[get_backend] = AuthBackend
    with TestClient(app) as client:
        response = client.post("/api/auth/login", json={"login_id": "fixture", "password": "secret"})
    assert response.status_code == 200
    assert response.json()["user"]["must_change_password"] is True
    assert "opaque-fixture-token" not in response.text
    cookie = response.headers["set-cookie"].lower()
    assert "oke_session=" in cookie and "httponly" in cookie and "secure" in cookie
    assert "samesite=lax" in cookie and "path=/" in cookie


def test_logout_revokes_current_session_and_deletes_cookie():
    app = create_app(Settings(_env_file=None))

    def current_user(request: Request):
        request.state.auth_session_id = 19
        return UserSummary(id=7, name="박서연", dept="재무팀", role="employee",
                           must_change_password=False)

    app.dependency_overrides[get_backend] = AuthBackend
    app.dependency_overrides[get_current_user] = current_user
    with TestClient(app) as client:
        client.cookies.set("oke_session", "fixture")
        response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert 'oke_session=""' in response.headers["set-cookie"]
    assert "max-age=0" in response.headers["set-cookie"].lower()


def test_first_login_user_is_blocked_from_employee_routes(contract_harness):
    app, client, backend, user = contract_harness
    user.must_change_password = True
    client.cookies.set("oke_session", "fixture")
    response = client.get("/api/my-requests")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "password_change_required"
    assert backend.operations == []


def test_non_it_admin_claim_is_not_authorized(contract_harness):
    app, client, backend, user = contract_harness
    user.role = "admin"
    client.cookies.set("oke_session", "fixture")
    response = client.get("/api/admin/users")
    assert response.status_code == 403
    assert backend.operations == []


def test_employee_cannot_read_or_modify_admin_tickets(contract_harness):
    _, client, backend, _ = contract_harness
    client.cookies.set("oke_session", "fixture")
    assert client.get("/api/admin/tickets").status_code == 403
    assert client.patch("/api/admin/tickets/1", json={"status": "resolved"}).status_code == 403
    assert backend.operations == []


def test_unconfigured_session_secret_fails_closed():
    app = create_app(Settings(_env_file=None, database_url=None, session_secret=None))
    with TestClient(app) as client:
        client.cookies.set("oke_session", "untrusted")
        response = client.get("/api/auth/me")
    assert response.status_code == 503
    assert "untrusted" not in response.text
