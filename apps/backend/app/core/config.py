"""P0-1 permits startup without DB or external service credentials."""

from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        alias_generator=str.upper,
        populate_by_name=True,
        hide_input_in_errors=True,
        extra="ignore",
    )

    service_mode: Literal["practice", "app"] = "app"
    database_url: SecretStr | None = Field(default=None, repr=False, exclude=True)
    n8n_webhook_url: AnyHttpUrl | None = None
    n8n_webhook_key: SecretStr | None = Field(default=None, repr=False, exclude=True)
    internal_api_key: SecretStr | None = Field(default=None, repr=False, exclude=True)
    data_api_url: AnyHttpUrl | None = None
    data_api_key: SecretStr | None = Field(default=None, repr=False, exclude=True)
    session_secret: SecretStr | None = Field(default=None, repr=False, exclude=True)
    bootstrap_admin_password: SecretStr | None = Field(default=None, repr=False, exclude=True)
    backend_origin: AnyHttpUrl = AnyHttpUrl("http://127.0.0.1:8000")
