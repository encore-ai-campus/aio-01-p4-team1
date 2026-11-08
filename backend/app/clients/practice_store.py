"""C05 practice-store adapter. Live data-api response details remain unverified."""

from collections.abc import Mapping

import httpx
from pydantic import ValidationError

from app.api.errors import PublicApiError
from app.core.config import Settings
from app.schemas.alerts import AlertCreate, AlertStoredResponse, DlqCreate, StoredResponse
from app.schemas.tickets import TicketCreate, TicketCreated

PRACTICE_TIMEOUT_SECONDS = 0.6
PRACTICE_TICKET_TIMEOUT_SECONDS = 1.0


class PracticeStoreClient:
    def __init__(self, settings: Settings, *, transport: httpx.BaseTransport | None = None):
        if not settings.data_api_url or not settings.data_api_key or not settings.data_api_key.get_secret_value():
            raise PublicApiError(503, "service_unavailable", "저장 서비스를 사용할 수 없습니다.")
        self.base_url = str(settings.data_api_url).rstrip("/") + "/"
        self.key = settings.data_api_key.get_secret_value()
        self.transport = transport

    def _post(self, path: str, body: Mapping[str, object]) -> tuple[int, object]:
        try:
            timeout_seconds = (PRACTICE_TICKET_TIMEOUT_SECONDS if path == "tickets"
                               else PRACTICE_TIMEOUT_SECONDS)
            timeout = httpx.Timeout(timeout_seconds, connect=0.3)
            with httpx.Client(base_url=self.base_url,
                              headers={"X-Api-Key": self.key}, timeout=timeout,
                              follow_redirects=False, transport=self.transport) as client:
                response = client.post(path, json=dict(body))
            return response.status_code, response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            raise PublicApiError(503, "service_unavailable", "저장 서비스를 사용할 수 없습니다.") from None

    @staticmethod
    def _object(payload: object) -> Mapping[str, object]:
        if not isinstance(payload, Mapping):
            raise PublicApiError(503, "service_unavailable", "저장 서비스 응답을 확인할 수 없습니다.")
        return payload

    def create_ticket(self, body: TicketCreate) -> TicketCreated:
        status, payload = self._post("tickets", body.model_dump())
        result = self._object(payload)
        try:
            ticket = TicketCreated.model_validate(result)
        except ValidationError:
            raise PublicApiError(503, "service_unavailable", "저장 서비스 응답을 확인할 수 없습니다.") from None
        if (status, ticket.duplicate) not in {(201, False), (200, True)}:
            raise PublicApiError(503, "service_unavailable", "저장 서비스 응답을 확인할 수 없습니다.")
        return ticket

    def create_alert(self, body: AlertCreate) -> AlertStoredResponse:
        status, payload = self._post("alerts", body.model_dump(exclude_none=True))
        result = self._object(payload)
        if status != 200:
            raise PublicApiError(503, "service_unavailable", "저장 서비스 응답을 확인할 수 없습니다.")
        duplicate = result.get("duplicate")
        stored, count = result.get("stored"), result.get("count")
        # The known practice compatibility response omits duplicate for a new write only.
        if duplicate is None and stored == 1:
            duplicate = False
        try:
            ack = AlertStoredResponse.model_validate(
                {"stored": stored, "count": count, "duplicate": duplicate})
        except ValidationError:
            raise PublicApiError(503, "service_unavailable", "저장 서비스 응답을 확인할 수 없습니다.") from None
        if (ack.stored, ack.duplicate) not in {(1, False), (0, True)}:
            raise PublicApiError(503, "service_unavailable", "저장 서비스 응답을 확인할 수 없습니다.")
        return ack

    def create_dlq(self, body: DlqCreate) -> StoredResponse:
        data = body.model_dump(exclude_none=True)
        data["request_id"] = body.request_id
        status, payload = self._post("dlq", data)
        result = self._object(payload)
        if status != 200:
            raise PublicApiError(503, "service_unavailable", "저장 서비스 응답을 확인할 수 없습니다.")
        try:
            return StoredResponse.model_validate(result)
        except ValidationError:
            raise PublicApiError(503, "service_unavailable", "저장 서비스 응답을 확인할 수 없습니다.") from None
