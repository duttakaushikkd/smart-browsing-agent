from functools import lru_cache

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP tool server configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Smart Browsing Agent MCP Tool Server"
    environment: str = "local"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 9000

    browser_service_url: AnyHttpUrl = "http://localhost:8080"  # type: ignore[assignment]
    browser_timeout_seconds: float = 20.0

    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "169.254.169.254", "::1"]
    )

    tool_timeout_seconds: float = 60.0
    max_tool_retries: int = 2

    @field_validator("allowed_domains", "blocked_domains", mode="before")
    @classmethod
    def parse_csv_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return [item.lower() for item in value]


@lru_cache
def get_settings() -> Settings:
    return Settings()
