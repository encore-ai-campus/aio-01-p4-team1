from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator

from app.schemas.common import ContractModel, EntityId, NonEmpty, OkResponse

Password = Annotated[SecretStr, Field(min_length=1, repr=False, exclude=True)]
NewPassword = Annotated[SecretStr, Field(min_length=12, repr=False, exclude=True)]


def check_password_classes(value: SecretStr) -> SecretStr:
    text = value.get_secret_value()
    groups = [any("a" <= c <= "z" for c in text), any("A" <= c <= "Z" for c in text),
              any("0" <= c <= "9" for c in text),
              any(not c.isalnum() and not c.isspace() for c in text)]
    if sum(groups) < 3:
        raise ValueError("password must use at least three character groups")
    return value


class UserSummary(ContractModel):
    id: EntityId
    name: NonEmpty
    dept: NonEmpty
    role: Literal["employee", "admin"]
    must_change_password: bool


class LoginRequest(ContractModel):
    login_id: NonEmpty
    password: Password


class LoginResponse(ContractModel):
    user: UserSummary


class ChangePasswordRequest(ContractModel):
    current_password: Password
    new_password: NewPassword

    _check_new = field_validator("new_password")(check_password_classes)


class ChangePasswordResponse(OkResponse):
    must_change_password: Literal[False] = False
