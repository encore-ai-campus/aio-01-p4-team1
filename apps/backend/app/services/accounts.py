from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import PublicApiError
from app.core.security import hash_password, validate_password
from app.db.models import Employee, User
from app.repositories.sessions import delete_user_sessions, revoke_user_sessions
from app.repositories.users import get_user_identity, list_employees, list_users


class AccountError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def lock_accounts(session: Session):
    # Share the bootstrap lock so first-admin setup and later account changes serialize.
    session.execute(text("SELECT pg_advisory_xact_lock(8060006)"))


def employee_items(session: Session):
    return [{"id": employee.id, "name": employee.name, "dept": employee.dept, "user_id": user_id}
            for employee, user_id in list_employees(session)]


def create_employee(session: Session, *, name: str, dept: str):
    lock_accounts(session)
    if session.scalar(select(Employee.id).where(Employee.name == name)) is not None:
        raise AccountError(409, "employee_conflict", "이미 등록된 직원입니다.")
    employee = Employee(name=name, dept=dept)
    session.add(employee)
    try:
        session.flush()
    except IntegrityError:
        raise AccountError(409, "employee_conflict", "이미 등록된 직원입니다.") from None
    return {"id": employee.id, "name": employee.name, "dept": employee.dept,
            "user_id": None}


def account_items(session: Session):
    return [account_view(user, employee) for user, employee in list_users(session)]


def account_view(user: User, employee: Employee):
    return {"id": user.id, "employee_id": user.employee_id, "login_id": user.login_id,
            "name": employee.name, "dept": employee.dept, "role": user.role,
            "is_active": user.is_active, "must_change_password": user.must_change_password}


def create_account(session: Session, *, employee_id: int, login_id: str, password: str):
    lock_accounts(session)
    employee = session.get(Employee, employee_id)
    if employee is None:
        raise AccountError(400, "invalid_employee", "직원 정보를 확인해 주세요.")
    if session.scalar(select(User.id).where((User.employee_id == employee_id) | (User.login_id == login_id))):
        raise AccountError(409, "account_conflict", "이미 발급된 계정입니다.")
    try:
        validate_password(password, employee_name=employee.name, login_id=login_id)
    except ValueError:
        raise AccountError(400, "invalid_password", "비밀번호 기준을 확인해 주세요.") from None
    user = User(employee_id=employee.id, login_id=login_id, password_hash=hash_password(password),
                role="admin" if employee.dept == "IT팀" else "employee",
                is_active=True, must_change_password=True)
    session.add(user)
    try:
        session.flush()
    except IntegrityError:
        raise AccountError(409, "account_conflict", "이미 발급된 계정입니다.") from None
    return account_view(user, employee)


def update_active(session: Session, *, user_id: int, actor_id: int, is_active: bool):
    lock_accounts(session)
    pair = get_user_identity(session, user_id)
    if pair is None:
        raise AccountError(404, "not_found", "계정을 찾을 수 없습니다.")
    user, employee = pair
    if not is_active and user.is_active:
        if user.id == actor_id:
            raise AccountError(409, "self_deactivation", "본인 계정은 비활성화할 수 없습니다.")
        if user.role == "admin" and employee.dept == "IT팀":
            admins = session.scalar(select(func.count()).select_from(User).join(Employee)
                .where(User.role == "admin", User.is_active.is_(True), Employee.dept == "IT팀"))
            if admins <= 1:
                raise AccountError(409, "last_admin", "마지막 활성 관리자는 비활성화할 수 없습니다.")
        user.is_active = False
        revoke_user_sessions(session, user.id)
    elif is_active:
        user.is_active = True
    session.flush()
    return account_view(user, employee)


def reset_password(session: Session, *, user_id: int, password: str):
    lock_accounts(session)
    pair = get_user_identity(session, user_id)
    if pair is None:
        raise AccountError(404, "not_found", "계정을 찾을 수 없습니다.")
    user, employee = pair
    try:
        validate_password(password, employee_name=employee.name, login_id=user.login_id)
    except ValueError:
        raise AccountError(400, "invalid_password", "비밀번호 기준을 확인해 주세요.") from None
    user.password_hash = hash_password(password)
    user.must_change_password = True
    revoke_user_sessions(session, user.id)
    session.flush()
    return {"ok": True, "must_change_password": True}


def delete_account(session: Session, *, user_id: int, actor_id: int):
    lock_accounts(session)
    pair = get_user_identity(session, user_id)
    if pair is None:
        raise AccountError(404, "not_found", "계정을 찾을 수 없습니다.")
    user, _employee = pair
    if user.id == actor_id or user.role == "admin":
        raise PublicApiError(400, "account_delete_forbidden",
                             "관리자 본인 계정은 삭제할 수 없습니다.")
    delete_user_sessions(session, user.id)
    session.delete(user)
    session.flush()
    return {"ok": True, "message": "계정이 삭제되었습니다."}
