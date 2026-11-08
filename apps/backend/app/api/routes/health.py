from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.readiness import check_database

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/live", response_model=LivenessResponse)
def liveness() -> LivenessResponse:
    """Process liveness only; intentionally independent of the DB."""
    return LivenessResponse()


@router.get("/ready", responses={503: {"description": "Database prerequisites unavailable"}})
def readiness(request: Request) -> JSONResponse:
    result = check_database(request.app.state.settings)
    return JSONResponse(status_code=200 if result["status"] == "ready" else 503,
                        content={**result, "scope": "database", "service_mode": request.app.state.settings.service_mode})
