from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.api.errors import PublicApiError
from app.core.security import (hash_password, hash_session_token, new_session_token,
                               validate_password, verify_password)
from app.db.models import Employee, Session as LoginSession, User
from app.repositories.sessions import revoke_session, revoke_user_sessions
from app.repositories.users import get_user_by_login, get_user_identity
from app.services.accounts import lock_accounts

SESSION_HOURS = 8


class LoginError(Exception):
    pass


def user_summary(user: User, employee: Employee):
    return {"id": user.id, "name": employee.name, "dept": employee.dept,
            "role": user.role, "must_change_password": user.must_change_password}


def authenticate(session: Session, *, login_id: str, password: str, session_secret: str):
    user = get_user_by_login(session, login_id)
    if user is None or not user.is_active or not verify_password(user.password_hash, password):
        raise LoginError
    pair = get_user_identity(session, user.id)
    if pair is None:
        raise LoginError
    user, employee = pair
    token = new_session_token()
    session.add(LoginSession(user_id=user.id, token_hash=hash_session_token(token, session_secret),
                             expires_at=datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)))
    session.flush()
    return user_summary(user, employee), token


def load_current_user(session: Session, *, token: str, session_secret: str):
    from app.repositories.sessions import find_active_session
    found = find_active_session(session, hash_session_token(token, session_secret), datetime.now(timezone.utc))
    if found is None:
        return None
    login_session, user = found
    identity = get_user_identity(session, user.id)
    if identity is None:
        return None
    user, employee = identity
    return user_summary(user, employee), login_session.id


def logout(session: Session, session_id: int):
    revoke_session(session, session_id)


def change_password(session: Session, *, principal_id: int, session_id: int,
                    current_password: str, new_password: str):
    lock_accounts(session)
    pair = get_user_identity(session, principal_id)
    if pair is None:
        raise PublicApiError(401, "unauthorized", "로그인이 필요합니다.")
    user, employee = pair
    if not verify_password(user.password_hash, current_password):
        raise PublicApiError(401, "unauthorized", "현재 비밀번호를 확인해 주세요.")
    if not user.is_active:
        raise PublicApiError(401, "unauthorized", "로그인이 필요합니다.")
    try:
        validate_password(new_password, employee_name=employee.name, login_id=user.login_id)
    except ValueError:
        raise PublicApiError(400, "invalid_password", "새 비밀번호 기준을 확인해 주세요.") from None
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    revoke_user_sessions(session, user.id)
    session.flush()
    return {"ok": True, "must_change_password": False}


