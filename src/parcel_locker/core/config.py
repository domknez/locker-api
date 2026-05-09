from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+asyncpg://parcel:parcel@db:5432/parcel",
        description="SQLAlchemy async URL.",
    )
    database_echo: bool = False

    api_bearer_token: str = Field(
        default="dev-secret-change-me",
        min_length=8,
        description="Static token required for write endpoints.",
    )

    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "parcel-locker-service/0.1"
    nominatim_timeout_seconds: float = 5.0

    parcel_submission_ttl_hours: int = Field(default=48, gt=0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
