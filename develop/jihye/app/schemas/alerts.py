from datetime import datetime
from typing import Annotated, Any

from pydantic import Field

from app.schemas.common import ContractModel, EntityId, NonEmpty, RequestId


class AlertCreate(ContractModel):
    workflow: NonEmpty
    node: NonEmpty
    message: NonEmpty
    severity: NonEmpty
    ticket_id: NonEmpty | None = None
    event_key: NonEmpty | None = None


class StoredResponse(ContractModel):
    stored: Annotated[int, Field(ge=0)]
    count: Annotated[int, Field(ge=0)]


class AlertView(ContractModel):
    id: EntityId
    ticket_id: str | None
    workflow: NonEmpty
    node: NonEmpty
    message: NonEmpty
    severity: NonEmpty
    created_at: datetime


class DlqCreate(ContractModel):
    request_id: RequestId | None
    workflow: NonEmpty
    node: NonEmpty
    reason: NonEmpty
    safe_payload: dict[str, Any] = Field(description="호출자가 비밀·개인정보를 제거한 입력. 저장 시 검사는 P1")
    execution_ref: NonEmpty | None = None
