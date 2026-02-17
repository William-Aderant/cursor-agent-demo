"""Application settings via pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def _url_to_async(url: str) -> str:
    """Convert postgresql:// to postgresql+asyncpg:// for async engine."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    """App settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database (set DATABASE_URL or DEV_DATABASE_URL; Alembic and app use DATABASE_URL)
    DATABASE_URL: str | None = None
    DEV_DATABASE_URL: str | None = None

    @property
    def database_url(self) -> str:
        return (
            self.DATABASE_URL
            or self.DEV_DATABASE_URL
            or "postgresql://user:password@localhost:5432/url_monitor"
        )

    # Async URL for SQLAlchemy
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return _url_to_async(self.database_url)

    # Auth (BFF)
    OIDC_PROVIDER: Literal["cognito", "okta"] = "cognito"
    OIDC_ISSUER: str = ""
    OIDC_AUDIENCE: str = ""
    OIDC_CLIENT_SECRET: str = ""
    AUTH_SESSION_COOKIE_NAME: str = "url_monitor_session"
    AUTH_SESSION_TTL_SECONDS: int = 3600
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
