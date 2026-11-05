from datetime import datetime

from pydantic import Field

from app.schemas.common import Attempt, ContractModel, Question, RequestId
from app.schemas.support import SupportResponse, TicketRef


class InquiryView(ContractModel):
    """H03 draft list item; ownership and persistence follow in P1."""
    request_id: RequestId
    question: Question
    attempt: Attempt
    result: SupportResponse | None
    ticket: TicketRef | None
    created_at: datetime = Field(description="문의 생성 시각")
