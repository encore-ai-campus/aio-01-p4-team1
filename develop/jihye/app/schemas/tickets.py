from datetime import datetime

from pydantic import Field

from app.schemas.common import ContractModel, EntityId, NonEmpty, Priority, RequestId, TicketStatus


class TicketCreate(ContractModel):
    key: RequestId
    title: NonEmpty
    requester: NonEmpty
    category: NonEmpty
    priority: Priority


class TicketCreated(ContractModel):
    ticket_id: NonEmpty
    duplicate: bool


class TicketPatch(ContractModel):
    status: TicketStatus
    assignee: EntityId | None = Field(default=None, description="IT팀 employees.id. 생략/해제 구분은 H03 초안")
    reply: str | None = None


class TicketView(ContractModel):
    """Administrator list/single DTO; excludes original data-api ticket states."""
    id: EntityId
    ticket_id: NonEmpty
    request_id: RequestId
    requester: NonEmpty
    title: NonEmpty
    category: NonEmpty
    priority: Priority
    status: TicketStatus
    assignee: EntityId | None
    reply: str | None
    question: str | None = None
    created_at: datetime
    updated_at: datetime
