from fastapi import APIRouter

from app.api.deps import Backend, CurrentUser
from app.schemas.auth import (ChangePasswordRequest, ChangePasswordResponse, LoginRequest,
                              LoginResponse, UserSummary)
from app.schemas.common import OkResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, backend: Backend):
    return await backend.execute("login", body=body)


@router.post("/logout", response_model=OkResponse)
async def logout(user: CurrentUser, backend: Backend):
    return await backend.execute("logout", principal=user)


@router.get("/me", response_model=UserSummary)
async def me(user: CurrentUser):
    return user


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(body: ChangePasswordRequest, user: CurrentUser, backend: Backend):
    return await backend.execute("change_password", body=body, principal=user)
