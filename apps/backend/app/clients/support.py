"""C02 HTTP adapter. It preserves the shared support response and safe errors."""

import anyio
import httpx
from pydantic import ValidationError

from app.api.errors import PublicApiError, SupportInputError
from app.core.config import Settings
from app.schemas.support import (SupportCodesResponse, SupportRequest, SupportResponse,
                                 validate_support_response)

CONNECT_TIMEOUT_SECONDS = 3.0
REQUEST_TIMEOUT_SECONDS = 30.0


class SupportClient:
    def __init__(self, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    async def ask(self, payload: SupportRequest) -> SupportResponse:
        url = self.settings.n8n_webhook_url
        key = self.settings.n8n_webhook_key
        if not url or not key or not key.get_secret_value():
            raise PublicApiError(503, "service_unavailable", "문의 처리 서비스를 사용할 수 없습니다.")

        try:
            timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS,
                                    connect=CONNECT_TIMEOUT_SECONDS)
            async with httpx.AsyncClient(timeout=timeout, transport=self.transport,
                                         follow_redirects=False) as client:
                with anyio.fail_after(REQUEST_TIMEOUT_SECONDS):
                    response = await client.post(str(url),
                        headers={"X-Team-Key": key.get_secret_value()},
                        json=payload.model_dump(exclude_none=True))
        except (TimeoutError, httpx.TimeoutException):
            raise PublicApiError(504, "gateway_timeout", "문의 처리 시간이 초과되었습니다.") from None
        except httpx.HTTPError:
            raise PublicApiError(503, "service_unavailable", "문의 처리 서비스를 사용할 수 없습니다.") from None

        if response.status_code == 400:
            try:
                codes = SupportCodesResponse.model_validate(response.json())
            except (ValueError, ValidationError):
                raise PublicApiError(503, "service_unavailable",
                                     "문의 처리 서비스를 사용할 수 없습니다.") from None
            raise SupportInputError(codes.model_dump(exclude_unset=True))
        if response.status_code != 200:
            raise PublicApiError(503, "service_unavailable", "문의 처리 서비스를 사용할 수 없습니다.")
        try:
            return validate_support_response(response.json(), payload.request_id)
        except (ValueError, ValidationError, TypeError):
            raise PublicApiError(503, "service_unavailable",
                                 "문의 처리 서비스 응답을 확인할 수 없습니다.") from None


def build_support_client(settings: Settings) -> SupportClient:
    return SupportClient(settings)
