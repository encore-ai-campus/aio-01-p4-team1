"""Public errors never include validation input, context or exception text."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.schemas.common import ErrorDetail, ErrorResponse


class PublicApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message


class SupportInputError(Exception):
    """Already-public C02 validation response; never wrap its codes body."""

    def __init__(self, payload: dict):
        super().__init__("support input rejected")
        self.payload = payload


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(),
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(PublicApiError)
    async def public_api_error(request: Request, exc: PublicApiError) -> JSONResponse:
        return error_response(exc.status, exc.code, exc.message)

    @app.exception_handler(SupportInputError)
    async def support_input_error(request: Request, exc: SupportInputError) -> JSONResponse:
        return JSONResponse(status_code=400, content=exc.payload)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Fine-grained field codes remain a JH-H03 proposal.
        return error_response(400, "invalid_input", "입력값을 확인해 주세요.")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        codes = {
            400: ("invalid_input", "입력값을 확인해 주세요."),
            401: ("unauthorized", "로그인이 필요합니다."),
            403: ("forbidden", "접근 권한이 없습니다."),
            404: ("not_found", "요청한 항목을 찾을 수 없습니다."),
            405: ("method_not_allowed", "허용되지 않은 요청 방식입니다."),
            409: ("conflict", "요청이 기존 기록과 충돌합니다."),
            501: ("not_implemented", "아직 구현되지 않은 기능입니다."),
        }
        code, message = codes.get(exc.status_code, ("http_error", "요청을 처리할 수 없습니다."))
        return error_response(exc.status_code, code, message)

    @app.exception_handler(ResponseValidationError)
    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception) -> JSONResponse:
        return error_response(500, "internal_error", "요청을 처리할 수 없습니다.")
