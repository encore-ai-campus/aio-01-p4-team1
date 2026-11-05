"""Fail-closed seams for P0-2. Real session/key verification and services follow in P1."""

from typing import Annotated, Protocol

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyCookie, APIKeyHeader

from app.schemas.auth import UserSummary
from app.api.errors import PublicApiError

session_cookie = APIKeyCookie(name="oke_session", auto_error=False)
internal_key = APIKeyHeader(name="X-Api-Key", auto_error=False)


class ContractBackend(Protocol):
    async def execute(self, operation: str, *, body: object = None,
                      principal: UserSummary | None = None, entity_id: int | None = None) -> object: ...


class UnavailableBackend:
    async def execute(self, operation: str, **kwargs: object) -> object:
        raise HTTPException(501)


def get_backend() -> ContractBackend:
    return UnavailableBackend()


def get_current_user(token: Annotated[str | None, Security(session_cookie)]) -> UserSummary:
    if not token:
        raise HTTPException(401)
    # A cookie's presence never constitutes authentication.
    raise HTTPException(501)


def require_employee(user: Annotated[UserSummary, Depends(get_current_user)]) -> UserSummary:
    if user.must_change_password:
        raise PublicApiError(403, "password_change_required", "비밀번호를 먼저 변경해 주세요.")
    return user


def require_admin(user: Annotated[UserSummary, Depends(require_employee)]) -> UserSummary:
    if user.role != "admin" or user.dept != "IT팀":
        raise HTTPException(403)
    return user


def require_internal_key(key: Annotated[str | None, Security(internal_key)]) -> None:
    if not key:
        raise HTTPException(401)
    # Verification against configured credentials is not implemented in P0-2.
    raise HTTPException(501)


Backend = Annotated[ContractBackend, Depends(get_backend)]
CurrentUser = Annotated[UserSummary, Depends(get_current_user)]
Employee = Annotated[UserSummary, Depends(require_employee)]
Admin = Annotated[UserSummary, Depends(require_admin)]
