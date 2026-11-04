from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.routes.health import router as health_router
from app.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    application = FastAPI(title="오케퐁 업무 API", version="0.1.0")
    application.state.settings = settings if settings is not None else Settings()
    register_error_handlers(application)
    application.include_router(health_router)
    return application


app = create_app()
