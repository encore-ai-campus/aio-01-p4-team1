"""Password primitives shared by explicit bootstrap and future account services."""

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from pydantic import SecretStr

from app.schemas.auth import check_password_classes

_hasher = PasswordHasher(type=Type.ID)


def validate_password(password: str, *, employee_name: str, login_id: str) -> None:
    if len(password) < 12 or any(value.casefold() in password.casefold() for value in (employee_name, login_id)):
        raise ValueError("bootstrap_password_policy")
    try:
        check_password_classes(SecretStr(password))
    except ValueError:
        raise ValueError("bootstrap_password_policy") from None


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(encoded: str, password: str) -> bool:
    try:
        return _hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False
