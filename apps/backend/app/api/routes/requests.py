from fastapi import APIRouter

from app.api.deps import Backend, Employee
from app.schemas.common import ItemsResponse
from app.schemas.inquiries import InquiryView

router = APIRouter(tags=["requests"])


@router.get("/api/my-requests", response_model=ItemsResponse[InquiryView])
async def my_requests(user: Employee, backend: Backend):
    return await backend.execute("my_requests", principal=user)
