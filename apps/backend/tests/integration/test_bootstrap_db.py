"""Rollback-only tests against the dedicated PostgreSQL, never VM bootstrap."""

import os
import secrets

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clients.data_api import EXPECTED_EMPLOYEES
from app.core.security import verify_password
from app.db.models import Employee, User
from app.db.session import create_db_engine
from app.services.bootstrap import BootstrapError, bootstrap_admin, seed_employees

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires isolated DB opt-in",
)]


@pytest.fixture
def db():
    engine = create_db_engine()
    with engine.connect() as connection:
        tx = connection.begin()
        with Session(bind=connection) as session:
            assert session.scalar(select(func.count()).select_from(Employee)) == 0
            assert session.scalar(select(func.count()).select_from(User)) == 0
            yield session
        tx.rollback()
    engine.dispose()


def test_seed_and_bootstrap_repeat_preserves_hash(db):
    assert seed_employees(db, EXPECTED_EMPLOYEES) == 6
    assert seed_employees(db, EXPECTED_EMPLOYEES) == 0
    password = secrets.token_urlsafe(24) + "aA1!"
    assert bootstrap_admin(db, employee_name="김민지", login_id="fixture-admin", password=password) == 1
    user = db.scalar(select(User))
    encoded = user.password_hash
    assert user.role == "admin" and user.is_active and user.must_change_password
    assert verify_password(encoded, password)
    assert bootstrap_admin(db, employee_name="김민지", login_id="fixture-admin", password=secrets.token_urlsafe(24)) == 0
    assert db.scalar(select(User)).password_hash == encoded
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_invalid_seed_does_not_write(db):
    with pytest.raises(BootstrapError):
        seed_employees(db, {"invalid": "IT팀"})
    assert db.scalar(select(func.count()).select_from(Employee)) == 0


def test_existing_department_is_not_overwritten(db):
    db.add(Employee(name="이준호", dept="변경"))
    db.flush()
    with pytest.raises(BootstrapError, match="employee_database_mismatch"):
        seed_employees(db, EXPECTED_EMPLOYEES)
    assert db.scalar(select(Employee)).dept == "변경"


@pytest.mark.parametrize("employee", ["박서연", "unknown"])
def test_bootstrap_requires_it_employee(db, employee):
    seed_employees(db, EXPECTED_EMPLOYEES)
    with pytest.raises(BootstrapError, match="bootstrap_requires_it_employee"):
        bootstrap_admin(db, employee_name=employee, login_id="fixture-admin", password="")
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_bootstrap_requires_seed_and_preserves_existing_account(db):
    with pytest.raises(BootstrapError, match="employee_seed_required"):
        bootstrap_admin(db, employee_name="김민지", login_id="fixture-admin", password="")
    seed_employees(db, EXPECTED_EMPLOYEES)
    employee = db.scalar(select(Employee).where(Employee.name == "김민지"))
    db.add(User(employee_id=employee.id, login_id="existing", password_hash="synthetic-hash", role="employee"))
    db.flush()
    with pytest.raises(BootstrapError, match="bootstrap_accounts_already_exist"):
        bootstrap_admin(db, employee_name="김민지", login_id="fixture-admin", password="")
    assert db.scalar(select(User)).role == "employee"
