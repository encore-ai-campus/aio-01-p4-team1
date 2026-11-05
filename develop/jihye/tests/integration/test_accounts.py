"""P1-1 service checks in the isolated PostgreSQL transaction; all rows roll back."""

import os
import secrets
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.core.security import hash_password, hash_session_token, verify_password
from app.db.models import Employee, Session as LoginSession, User
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from app.services.accounts import (AccountError, account_items, create_account,
                                   employee_items, reset_password, update_active)
from app.services.auth import (LoginError, authenticate, change_password, load_current_user,
                               logout)

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires isolated DB opt-in",
)]


@pytest.fixture
def db():
    engine = create_db_engine()
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, expire_on_commit=False) as session:
            for model in (Employee, User, LoginSession):
                assert session.scalar(select(func.count()).select_from(model)) == 0
            yield session
        transaction.rollback()
    engine.dispose()


def setup_accounts(db):
    it = Employee(name="fixture-it", dept="IT팀")
    staff = Employee(name="fixture-staff", dept="재무팀")
    db.add_all([it, staff])
    db.flush()
    admin_password = "Temporary-Admin-934!"
    staff_password = "Temporary-Staff-934!"
    admin = create_account(db, employee_id=it.id, login_id="fixture-admin",
                           password=admin_password)
    employee = create_account(db, employee_id=staff.id, login_id="fixture-staff",
                              password=staff_password)
    db.flush()
    admin_row = db.get(User, admin["id"])
    return it, staff, admin_row, admin_password, employee


def test_auth_session_password_rotation_and_account_views(db):
    _, _, admin, password, employee = setup_accounts(db)
    assert admin.role == "admin" and employee["role"] == "employee"
    assert admin.must_change_password is True
    assert len(employee_items(db)) == 2
    assert len(account_items(db)) == 2
    assert "password_hash" not in account_items(db)[0]

    secret = "test-session-signing-key"
    summary, raw_token = authenticate(db, login_id=admin.login_id, password=password,
                                      session_secret=secret)
    session_hash = hash_session_token(raw_token, secret)
    stored = db.scalar(select(LoginSession).where(LoginSession.token_hash == session_hash))
    assert stored is not None and stored.token_hash != raw_token
    assert summary["must_change_password"] is True
    assert load_current_user(db, token=raw_token, session_secret=secret)[0]["id"] == admin.id

    changed = change_password(db, principal_id=admin.id, session_id=stored.id,
                              current_password=password, new_password="Changed-Admin-934!")
    assert changed["must_change_password"] is False
    assert stored.revoked_at is not None
    assert load_current_user(db, token=raw_token, session_secret=secret) is None
    new_summary, new_token = authenticate(db, login_id=admin.login_id,
        password="Changed-Admin-934!", session_secret=secret)
    assert new_summary["must_change_password"] is False
    logout(db, db.scalar(select(LoginSession).where(
        LoginSession.token_hash == hash_session_token(new_token, secret))).id)
    assert load_current_user(db, token=new_token, session_secret=secret) is None
    with pytest.raises(LoginError):
        authenticate(db, login_id=admin.login_id, password="wrong", session_secret=secret)


def test_account_creation_duplicates_reset_and_session_revocation(db):
    it, staff, admin, _, employee = setup_accounts(db)
    with pytest.raises(AccountError) as conflict:
        create_account(db, employee_id=staff.id, login_id="different-id",
                       password="Temporary-Staff-934!")
    assert conflict.value.status == 409
    with pytest.raises(AccountError) as invalid:
        create_account(db, employee_id=999999, login_id="missing-employee",
                       password="Temporary-Staff-934!")
    assert invalid.value.status == 400

    secret = "test-session-signing-key"
    _, token = authenticate(db, login_id=employee["login_id"],
                            password="Temporary-Staff-934!", session_secret=secret)
    session = db.scalar(select(LoginSession).where(
        LoginSession.token_hash == hash_session_token(token, secret)))
    reset_password(db, user_id=employee["id"], password="Reset-Staff-934!X")
    assert session.revoked_at is not None
    staff_user = db.get(User, employee["id"])
    assert staff_user.must_change_password is True
    assert verify_password(staff_user.password_hash, "Reset-Staff-934!X")
    with pytest.raises(LoginError):
        authenticate(db, login_id=employee["login_id"], password="Temporary-Staff-934!",
                     session_secret=secret)


def test_inactive_account_expires_and_last_admin_guards(db):
    it, _, admin, password, _ = setup_accounts(db)
    secret = "test-session-signing-key"
    _, token = authenticate(db, login_id=admin.login_id, password=password, session_secret=secret)
    session = db.scalar(select(LoginSession).where(
        LoginSession.token_hash == hash_session_token(token, secret)))
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert load_current_user(db, token=token, session_secret=secret) is None

    with pytest.raises(AccountError) as last_admin:
        update_active(db, user_id=admin.id, actor_id=99999, is_active=False)
    assert last_admin.value.status == 409
    second_admin_employee = Employee(name="fixture-it-2", dept="IT팀")
    db.add(second_admin_employee)
    db.flush()
    second_admin = create_account(db, employee_id=second_admin_employee.id,
        login_id="fixture-admin-2", password="Temporary-Admin-934!")
    with pytest.raises(AccountError) as self_disable:
        update_active(db, user_id=admin.id, actor_id=admin.id, is_active=False)
    assert self_disable.value.status == 409
    update_active(db, user_id=admin.id, actor_id=second_admin["id"], is_active=False)
    assert db.get(User, admin.id).is_active is False
    assert session.revoked_at is not None


def test_00_real_http_login_first_change_admin_issue_and_logout():
    """Exercise P1-1 routes against the isolated migrated PostgreSQL, then clean fixtures."""
    engine = create_db_engine()
    suffix = uuid4().hex[:12]
    signing_secret = secrets.token_urlsafe(32)
    admin_password = "Start-Admin-938!"
    staff_password = "Start-Staff-938!"
    # A prior interrupted run may leave only this test's uniquely named fixtures.
    with create_session_factory(engine).begin() as session:
        stale = session.scalars(select(User).where(or_(
            User.login_id.like("p11-admin-%"), User.login_id.like("p11-staff-%"),
            User.login_id.like("p11-issued-%")))).all()
        stale_employee_ids = {user.employee_id for user in stale}
        stale_suffixes = {user.login_id.rsplit("-", 1)[-1] for user in stale}
        stale_user_ids = [user.id for user in stale]
        if stale_user_ids:
            session.execute(delete(LoginSession).where(LoginSession.user_id.in_(stale_user_ids)))
            session.execute(delete(User).where(User.id.in_(stale_user_ids)))
        if stale_employee_ids:
            session.execute(delete(Employee).where(Employee.id.in_(stale_employee_ids)))
        for stale_suffix in stale_suffixes:
            session.execute(delete(Employee).where(Employee.name == f"fixture-free-{stale_suffix}"))
    with create_session_factory(engine).begin() as session:
        for model in (Employee, User, LoginSession):
            assert session.scalar(select(func.count()).select_from(model)) == 0
        admin_employee = Employee(name=f"fixture-it-{suffix}", dept="IT팀")
        staff_employee = Employee(name=f"fixture-staff-{suffix}", dept="재무팀")
        free_employee = Employee(name=f"fixture-free-{suffix}", dept="영업팀")
        session.add_all([admin_employee, staff_employee, free_employee])
        session.flush()
        admin_user = User(employee_id=admin_employee.id, login_id=f"p11-admin-{suffix}",
            password_hash=hash_password(admin_password), role="admin", is_active=True,
            must_change_password=False)
        staff_user = User(employee_id=staff_employee.id, login_id=f"p11-staff-{suffix}",
            password_hash=hash_password(staff_password), role="employee", is_active=True,
            must_change_password=True)
        session.add_all([admin_user, staff_user])
        session.flush()
        admin_id, staff_id = admin_user.id, staff_user.id
        admin_employee_id, staff_employee_id, free_employee_id = (
            admin_employee.id, staff_employee.id, free_employee.id)

    settings = Settings(_env_file=None, database_url=SecretStr(os.environ["DATABASE_URL"]),
        session_secret=SecretStr(signing_secret), backend_origin="http://localhost")
    app = create_app(settings)
    try:
        with TestClient(app) as admin_client:
            assert admin_client.get("/api/admin/users").status_code == 401
            login = admin_client.post("/api/auth/login", json={
                "login_id": f"p11-admin-{suffix}", "password": admin_password})
            assert login.status_code == 200
            assert login.json()["user"]["role"] == "admin"
            assert admin_client.cookies.get("oke_session")
            assert "httponly" in login.headers["set-cookie"].lower()

            listed = admin_client.get("/api/admin/users")
            assert listed.status_code == 200
            assert all("password_hash" not in item for item in listed.json()["items"])
            issued = admin_client.post("/api/admin/users", json={
                "employee_id": free_employee_id, "login_id": f"p11-issued-{suffix}",
                "temporary_password": "Issued-Account-938!"})
            assert issued.status_code == 201
            assert issued.json()["role"] == "employee"
            assert issued.json()["must_change_password"] is True

            with TestClient(app) as staff_client:
                staff_login = staff_client.post("/api/auth/login", json={
                    "login_id": f"p11-staff-{suffix}", "password": staff_password})
                assert staff_login.status_code == 200
                old_staff_token = staff_client.cookies.get("oke_session")
                assert staff_client.get("/api/admin/users").status_code == 403
                blocked = staff_client.get("/api/my-requests")
                assert blocked.status_code == 403
                assert blocked.json()["error"]["code"] == "password_change_required"
                changed = staff_client.post("/api/auth/change-password", json={
                    "current_password": staff_password, "new_password": "Changed-Staff-938!"})
                assert changed.status_code == 200
                assert changed.json()["must_change_password"] is False
                with TestClient(app) as replay_client:
                    replay_client.cookies.set("oke_session", old_staff_token)
                    assert replay_client.get("/api/auth/me").status_code == 401

            old_admin_token = admin_client.cookies.get("oke_session")
            logout_response = admin_client.post("/api/auth/logout")
            assert logout_response.status_code == 200
            with TestClient(app) as replay_client:
                replay_client.cookies.set("oke_session", old_admin_token)
                assert replay_client.get("/api/auth/me").status_code == 401
    finally:
        with create_session_factory(engine).begin() as session:
            issued_user = session.scalar(select(User).where(User.login_id == f"p11-issued-{suffix}"))
            user_ids = [admin_id, staff_id]
            if issued_user is not None:
                user_ids.append(issued_user.id)
            session.execute(delete(LoginSession).where(LoginSession.user_id.in_(user_ids)))
            session.execute(delete(User).where(User.id.in_(user_ids)))
            session.execute(delete(Employee).where(Employee.id.in_(
                (admin_employee_id, staff_employee_id, free_employee_id))))
        engine.dispose()
