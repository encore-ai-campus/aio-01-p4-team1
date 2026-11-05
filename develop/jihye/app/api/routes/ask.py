from fastapi import APIRouter

from app.api.deps import Backend, Employee
from app.schemas.common import ErrorResponse
from app.schemas.support import AskRequest, SupportCodesResponse, SupportResponse

router = APIRouter(tags=["requests"])


@router.post("/api/ask", response_model=SupportResponse, response_model_exclude_unset=True,
             responses={400: {"model": ErrorResponse | SupportCodesResponse,
                              "description": "웹 입력 오류 또는 support의 공통 codes 본문"}})
async def ask(body: AskRequest, user: Employee, backend: Backend):
    return await backend.execute("ask", body=body, principal=user)
