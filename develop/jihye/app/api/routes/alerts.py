from fastapi import APIRouter, Depends

from app.api.deps import Admin, Backend, require_internal_key
from app.schemas.alerts import AlertCreate, AlertView, DlqCreate, StoredResponse
from app.schemas.common import ItemsResponse

router = APIRouter(tags=["alerts"])


@router.get("/api/admin/alerts", response_model=ItemsResponse[AlertView])
async def alerts(user: Admin, backend: Backend):
    return await backend.execute("alerts", principal=user)


@router.post("/alerts", response_model=StoredResponse, dependencies=[Depends(require_internal_key)])
async def create_alert(body: AlertCreate, backend: Backend):
    return await backend.execute("create_alert", body=body)


@router.post("/dlq", response_model=StoredResponse, dependencies=[Depends(require_internal_key)])
async def create_dlq(body: DlqCreate, backend: Backend):
    return await backend.execute("create_dlq", body=body)
