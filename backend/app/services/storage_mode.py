"""One selected C05 write target for each process mode."""

from enum import StrEnum

from app.core.config import Settings


class StorageMode(StrEnum):
    APP = "app"
    PRACTICE = "practice"


def storage_mode(settings: Settings) -> StorageMode:
    return StorageMode(settings.service_mode)
