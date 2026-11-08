from fastapi import APIRouter, Path
from typing import Annotated

from app.api.deps import Admin, Backend
from app.schemas.common import ItemsResponse
from app.schemas.users import (AccountView, CreateUserRequest, EmployeeAdminView,
                               DeleteAccountResponse, EmployeeCreateRequest,
                               ResetPasswordRequest, ResetPasswordResponse, UserActivePatch)

router = APIRouter(prefix="/api/admin", tags=["users"])
PathId = Annotated[int, Path(ge=1)]


@router.get("/employees", response_model=ItemsResponse[EmployeeAdminView])
async def employees(user: Admin, backend: Backend):
    return await backend.execute("employees", principal=user)


@router.post("/employees", response_model=EmployeeAdminView, status_code=201)
async def create_employee(body: EmployeeCreateRequest, user: Admin, backend: Backend):
    return await backend.execute("create_employee", body=body, principal=user)


@router.get("/users", response_model=ItemsResponse[AccountView])
async def users(user: Admin, backend: Backend):
    return await backend.execute("users", principal=user)


@router.post("/users", response_model=AccountView, status_code=201)
async def create_user(body: CreateUserRequest, user: Admin, backend: Backend):
    return await backend.execute("create_user", body=body, principal=user)


@router.patch("/users/{id}", response_model=AccountView)
async def update_user(id: PathId, body: UserActivePatch, user: Admin, backend: Backend):
    return await backend.execute("update_user", body=body, principal=user, entity_id=id)


@router.delete("/users/{id}", response_model=DeleteAccountResponse)
async def delete_user(id: PathId, user: Admin, backend: Backend):
    return await backend.execute("delete_user", principal=user, entity_id=id)


@router.post("/users/{id}/reset-password", response_model=ResetPasswordResponse)
async def reset_password(id: PathId, body: ResetPasswordRequest, user: Admin, backend: Backend):
    return await backend.execute("reset_password", body=body, principal=user, entity_id=id)
