from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Session as LoginSession, User


def find_active_session(session: Session, token_hash: str, now: datetime):
    return session.execute(select(LoginSession, User).join(User, User.id == LoginSession.user_id)
        .where(LoginSession.token_hash == token_hash, LoginSession.revoked_at.is_(None),
               LoginSession.expires_at > now, User.is_active.is_(True))).one_or_none()


def revoke_session(session: Session, session_id: int) -> None:
    row = session.get(LoginSession, session_id)
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)


def revoke_user_sessions(session: Session, user_id: int) -> int:
    now = datetime.now(timezone.utc)
    rows = session.scalars(select(LoginSession).where(LoginSession.user_id == user_id,
        LoginSession.revoked_at.is_(None))).all()
    for row in rows:
        row.revoked_at = now
    return len(rows)
