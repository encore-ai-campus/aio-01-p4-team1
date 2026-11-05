"""Shared request constraints and response envelopes."""

from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Question = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=500)
]
RequestId = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=64, pattern=r"\S")
]
Attempt = Annotated[int, Field(strict=True, ge=1)]
Context = Annotated[str, StringConstraints(strict=True, max_length=2000)]
EntityId = Annotated[int, Field(strict=True, ge=1)]
NonEmpty = Annotated[str, StringConstraints(strict=True, min_length=1, pattern=r"\S")]
Priority = Literal["normal", "high"]
TicketStatus = Literal["open", "in_progress", "resolved"]


class ContractModel(BaseModel):
    # Unknown request fields are ignored pending H03; never used for identity.
    model_config = ConfigDict(strict=True, hide_input_in_errors=True, extra="ignore")


T = TypeVar("T")


class ItemsResponse(ContractModel, Generic[T]):
    items: list[T]


class OkResponse(ContractModel):
    ok: Literal[True] = True


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
