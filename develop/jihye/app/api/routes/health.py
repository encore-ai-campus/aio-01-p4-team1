from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/live", response_model=LivenessResponse)
def liveness() -> LivenessResponse:
    """Process liveness only. DB readiness is implemented in P0-7."""
    return LivenessResponse()
