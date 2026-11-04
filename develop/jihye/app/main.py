from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.routes.health import router as health_router
from app.core.config import Settings
from app.api.routes import alerts, ask, auth, requests, tickets, users
from app.schemas.common import ErrorResponse


def create_app(settings: Settings | None = None) -> FastAPI:
    application = FastAPI(title="오케퐁 업무 API", version="0.1.0")
    application.state.settings = settings if settings is not None else Settings()
    register_error_handlers(application)
    application.include_router(health_router)
    for module in (auth, users, ask, requests, tickets, alerts):
        application.include_router(
            module.router,
            responses={code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 501)},
        )
    # Match the installed request-validation handler instead of advertising 422.
    original_openapi = application.openapi

    def contract_openapi():
        schema = original_openapi()
        schema["info"]["description"] = (
            "P0-2 계약 골격. 업무 서비스와 실제 인증·저장은 미구현(501). "
            "InquiryView/TicketView 및 security 세부 타입은 H03 초안입니다."
        )
        for path in schema["paths"].values():
            for operation in path.values():
                operation.get("responses", {}).pop("422", None)
        return schema

    application.openapi = contract_openapi
    return application


app = create_app()
