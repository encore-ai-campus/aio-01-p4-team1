from fastapi import APIRouter, Request, Response

from app.api.deps import Backend, CurrentUser
from app.schemas.auth import (ChangePasswordRequest, ChangePasswordResponse, LoginRequest,
                              LoginResponse, UserSummary)
from app.schemas.common import OkResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, backend: Backend, request: Request, response: Response):
    result = await backend.execute("login", body=body)
    token = result.pop("_token")
    settings = request.app.state.settings
    response.set_cookie("oke_session", token, max_age=8 * 60 * 60, httponly=True,
                        secure=settings.backend_origin.scheme == "https", samesite="lax", path="/")
    return result


@router.post("/logout", response_model=OkResponse)
async def logout(user: CurrentUser, backend: Backend, request: Request, response: Response):
    result = await backend.execute("logout", principal=user, session_id=request.state.auth_session_id)
    response.delete_cookie("oke_session", path="/", httponly=True,
                           secure=request.app.state.settings.backend_origin.scheme == "https", samesite="lax")
    return result


@router.get("/me", response_model=UserSummary)
async def me(user: CurrentUser):
    return user


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(body: ChangePasswordRequest, user: CurrentUser, backend: Backend,
                          request: Request, response: Response):
    result = await backend.execute("change_password", body=body, principal=user,
                                   session_id=request.state.auth_session_id)
    response.delete_cookie("oke_session", path="/", httponly=True,
                           secure=request.app.state.settings.backend_origin.scheme == "https", samesite="lax")
    return result
