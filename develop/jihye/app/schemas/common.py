"""Shared constraints; business request/response models follow in P0-2."""

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Question = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=500)
]
RequestId = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=64, pattern=r"\S")
]
Attempt = Annotated[int, Field(strict=True, ge=1)]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
