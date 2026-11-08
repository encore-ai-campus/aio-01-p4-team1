"""Cookie authentication and the scoped internal-key boundary for backend APIs."""

import hmac
from typing import Annotated, Protocol

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyCookie, APIKeyHeader

from app.schemas.auth import UserSummary
from app.api.errors import PublicApiError
from app.services.backend import DatabaseBackend

session_cookie = APIKeyCookie(name="oke_session", auto_error=False)
internal_key = APIKeyHeader(name="X-Api-Key", auto_error=False)


class ContractBackend(Protocol):
    async def execute(self, operation: str, *, body: object = None,
                      principal: UserSummary | None = None, entity_id: int | None = None,
                      session_id: int | None = None) -> object: ...


def get_backend(request: Request) -> ContractBackend:
    return DatabaseBackend(request.app.state.settings)


def get_current_user(request: Request, token: Annotated[str | None, Security(session_cookie)]) -> UserSummary:
    if not token:
        raise HTTPException(401)
    settings = request.app.state.settings
    if not settings.session_secret or not settings.session_secret.get_secret_value():
        raise HTTPException(503)
    from sqlalchemy.exc import SQLAlchemyError
    from app.db.session import create_db_engine, create_session_factory
    from app.db.session import DatabaseConfigurationError
    engine = None
    try:
        engine = create_db_engine(settings)
        with create_session_factory(engine).begin() as session:
            from app.services.auth import load_current_user
            result = load_current_user(session, token=token,
                                       session_secret=settings.session_secret.get_secret_value())
        if result is None:
            raise HTTPException(401)
        principal, session_id = result
        request.state.auth_session_id = session_id
        return UserSummary.model_validate(principal)
    except (SQLAlchemyError, DatabaseConfigurationError):
        raise HTTPException(503) from None
    finally:
        if engine is not None:
            engine.dispose()


def require_employee(user: Annotated[UserSummary, Depends(get_current_user)]) -> UserSummary:
    if user.must_change_password:
        raise PublicApiError(403, "password_change_required", "비밀번호를 먼저 변경해 주세요.")
    return user


def require_admin(user: Annotated[UserSummary, Depends(require_employee)]) -> UserSummary:
    if user.role != "admin" or user.dept != "IT팀":
        raise HTTPException(403)
    return user


def require_internal_key(request: Request,
                         key: Annotated[str | None, Security(internal_key)]) -> None:
    # The dependency reads only the configured server secret; it never reflects either value.
    configured = request.app.state.settings.internal_api_key
    if configured is None or not configured.get_secret_value():
        raise HTTPException(503)
    if not key or not hmac.compare_digest(key, configured.get_secret_value()):
        raise HTTPException(401)


Backend = Annotated[ContractBackend, Depends(get_backend)]
CurrentUser = Annotated[UserSummary, Depends(get_current_user)]
Employee = Annotated[UserSummary, Depends(require_employee)]
Admin = Annotated[UserSummary, Depends(require_admin)]
