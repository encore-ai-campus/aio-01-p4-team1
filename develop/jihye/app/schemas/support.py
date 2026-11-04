from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from app.schemas.common import Attempt, ContractModel, NonEmpty, Priority, Question, RequestId

FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]
Milliseconds = Annotated[float, Field(allow_inf_nan=False, ge=0)]


class AskRequest(ContractModel):
    question: Question
    request_id: RequestId | None = None
    attempt: Attempt = 1
    context: str | None = None


class SupportRequest(ContractModel):
    request_id: RequestId
    user: NonEmpty
    question: Question
    channel: Literal["web"] = "web"
    attempt: Attempt = 1
    context: str | None = None


class ExtensibleResponse(ContractModel):
    model_config = ConfigDict(extra="allow")


class SupportCodesResponse(ExtensibleResponse):
    codes: list[str]


class Source(ExtensibleResponse):
    doc: str
    section: str
    score: FiniteNumber


class TicketRef(ExtensibleResponse):
    ticket_id: NonEmpty
    priority: Priority
    duplicate: bool


class Security(ExtensibleResponse):
    """H03 draft typing; fields remain present and extra fields are preserved."""
    blocked_by: str | None
    reason: str | None
    masked: Annotated[int, Field(ge=0)]


class SupportResponse(ExtensibleResponse):
    request_id: RequestId
    route: Literal["자동 답변", "보완 질문", "담당자 이관", "권한 없음", "차단"]
    answer: str
    sources: list[Source]
    ticket: TicketRef | None
    agents: list[str]
    security: Security
    reason: str | None = None
    timings: dict[str, Milliseconds] | None = None


def validate_support_response(payload: object, expected_request_id: str) -> SupportResponse:
    result = SupportResponse.model_validate(payload)
    if result.request_id != expected_request_id:
        raise ValueError("support response request_id mismatch")
    return result
