from typing import Literal

from pydantic import field_validator

from app.schemas.auth import NewPassword, UserSummary, check_password_classes
from app.schemas.common import ContractModel, EntityId, NonEmpty, OkResponse


class EmployeeAdminView(ContractModel):
    id: EntityId
    name: NonEmpty
    dept: NonEmpty
    user_id: EntityId | None


class EmployeeCreateRequest(ContractModel):
    name: NonEmpty
    dept: NonEmpty


class AccountView(UserSummary):
    employee_id: EntityId
    login_id: NonEmpty
    is_active: bool


class CreateUserRequest(ContractModel):
    employee_id: EntityId
    login_id: NonEmpty
    temporary_password: NewPassword

    _check_password = field_validator("temporary_password")(check_password_classes)


class UserActivePatch(ContractModel):
    is_active: bool


class ResetPasswordRequest(ContractModel):
    temporary_password: NewPassword

    _check_password = field_validator("temporary_password")(check_password_classes)


class ResetPasswordResponse(OkResponse):
    must_change_password: Literal[True] = True


class DeleteAccountResponse(OkResponse):
    message: Literal["계정이 삭제되었습니다."]
