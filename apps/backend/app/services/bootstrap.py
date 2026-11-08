"""Explicit, repeatable bootstrap; caller owns commit/rollback."""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.clients.data_api import EXPECTED_EMPLOYEES
from app.core.security import hash_password, validate_password
from app.db.models import Employee, User


class BootstrapError(ValueError):
    pass


def lock_bootstrap(session: Session) -> None:
    session.execute(text("SELECT pg_advisory_xact_lock(8060006)"))


def seed_employees(session: Session, employees: dict[str, str]) -> int:
    if employees != EXPECTED_EMPLOYEES:
        raise BootstrapError("employee_source_mismatch")
    lock_bootstrap(session)
    existing = {item.name: item.dept for item in session.scalars(select(Employee))}
    if any(name not in employees or employees[name] != dept for name, dept in existing.items()):
        raise BootstrapError("employee_database_mismatch")
    for name, dept in employees.items():
        if name not in existing:
            session.add(Employee(name=name, dept=dept))
    session.flush()
    return len(employees) - len(existing)


def bootstrap_admin(session: Session, *, employee_name: str, login_id: str, password: str) -> int:
    if not login_id.strip():
        raise BootstrapError("login_id_required")
    lock_bootstrap(session)
    employees = list(session.scalars(select(Employee)))
    if {item.name: item.dept for item in employees} != EXPECTED_EMPLOYEES:
        raise BootstrapError("employee_seed_required")
    employee = next((item for item in employees if item.name == employee_name), None)
    if employee is None or employee.dept != "IT팀":
        raise BootstrapError("bootstrap_requires_it_employee")
    users = list(session.scalars(select(User)))
    if users:
        if any(user.employee_id == employee.id and user.login_id == login_id
               and user.role == "admin" and user.is_active for user in users):
            return 0
        raise BootstrapError("bootstrap_accounts_already_exist")
    validate_password(password, employee_name=employee_name, login_id=login_id)
    session.add(User(employee_id=employee.id, login_id=login_id,
                     password_hash=hash_password(password), role="admin",
                     is_active=True, must_change_password=True))
    session.flush()
    return 1
