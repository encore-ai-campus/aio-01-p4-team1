from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response

from app.api.deps import Admin, Backend, require_internal_key
from app.schemas.common import ItemsResponse
from app.schemas.tickets import TicketCreate, TicketCreated, TicketPatch, TicketView

router = APIRouter(tags=["tickets"])


@router.get("/api/admin/tickets", response_model=ItemsResponse[TicketView])
async def tickets(user: Admin, backend: Backend):
    return await backend.execute("tickets", principal=user)


@router.patch("/api/admin/tickets/{id}", response_model=TicketView)
async def update_ticket(id: Annotated[int, Path(ge=1)], body: TicketPatch, user: Admin, backend: Backend):
    return await backend.execute("update_ticket", body=body, principal=user, entity_id=id)


@router.post("/tickets", response_model=TicketCreated, status_code=201,
             responses={200: {"model": TicketCreated, "description": "동일 키의 기존 티켓"}},
             dependencies=[Depends(require_internal_key)])
async def create_ticket(body: TicketCreate, backend: Backend, response: Response):
    result = TicketCreated.model_validate(await backend.execute("create_ticket", body=body))
    response.status_code = 200 if result.duplicate else 201
    return result
