import json
import secrets

import httpx
import pytest

from app import cli
from app.clients.data_api import EXPECTED_EMPLOYEES, SourceError, fetch_employees, validate_employees
from app.core.security import hash_password, validate_password, verify_password


def rows():
    return [dict(name=name, dept=dept) for name, dept in EXPECTED_EMPLOYEES.items()]


def test_mock_employee_http_contract():
    def handler(request):
        assert request.url.path == "/employees"
        return httpx.Response(200, json={"employees": rows()})
    with httpx.Client(base_url="https://fixture.invalid/", transport=httpx.MockTransport(handler)) as client:
        assert fetch_employees(client) == EXPECTED_EMPLOYEES


@pytest.mark.parametrize("payload", [[], rows()[:-1], rows() + [dict(name="extra", dept="IT팀")],
    rows()[:-1] + [rows()[0]], [dict(name=row["name"], dept="변경") for row in rows()], None])
def test_source_mismatch_is_rejected(payload):
    with pytest.raises(SourceError, match="employee_source_mismatch"):
        validate_employees(payload)


@pytest.mark.parametrize("status,payload", [(401, {}), (500, {}), (302, {}), (200, []), (200, {"items": rows()})])
def test_http_failure_and_unknown_envelope(status, payload):
    with httpx.Client(base_url="https://fixture.invalid/", transport=httpx.MockTransport(
        lambda request: httpx.Response(status, json=payload))) as client:
        with pytest.raises(SourceError):
            fetch_employees(client)


def test_argon2id_and_identity_policy():
    password = secrets.token_urlsafe(24) + "aA1!"
    encoded = hash_password(password)
    assert encoded.startswith("$argon2id$")
    assert verify_password(encoded, password)
    assert not verify_password(encoded, secrets.token_urlsafe(24))
    for bad in ("short", "a" * 20, "admin-login-aA123!", "김민지-aA123456!"):
        with pytest.raises(ValueError):
            validate_password(bad, employee_name="김민지", login_id="admin-login")


def test_cli_missing_secrets_never_opens_db(monkeypatch, capsys):
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.setattr(cli, "create_db_engine", lambda *args: pytest.fail("must not connect"))
    assert cli.main(["bootstrap-admin", "--employee-name", "김민지", "--login-id", "fixture-admin"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "bootstrap_secrets_required"


def test_cli_does_not_infer_live_auth(monkeypatch, capsys):
    monkeypatch.delenv("DATA_API_EMPLOYEES_AUTH_HEADER", raising=False)
    monkeypatch.setattr(cli, "create_db_engine", lambda *args: pytest.fail("must not connect"))
    assert cli.main(["seed-employees"]) == 1
    assert "employee_source_configuration_required" in capsys.readouterr().out


def test_cli_masks_sensitive_exception(monkeypatch, capsys):
    secret = secrets.token_urlsafe(32)
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", secret)
    monkeypatch.setenv("SESSION_SECRET", secrets.token_urlsafe(32))
    def broken_engine(*args):
        raise ValueError(secret)
    monkeypatch.setattr(cli, "create_db_engine", broken_engine)
    assert cli.main(["bootstrap-admin", "--employee-name", "김민지", "--login-id", "fixture-admin"]) == 1
    output = capsys.readouterr()
    assert secret not in output.out + output.err
    assert json.loads(output.out)["error"] == "bootstrap_failed"
