from functools import lru_cache

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Smart Browsing Agent Planner"
    environment: str = "local"
    log_level: str = "INFO"

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4.1-mini"

    browser_service_url: AnyHttpUrl = "http://localhost:8080"  # type: ignore[assignment]
    browser_timeout_seconds: float = 20.0

    redis_url: str = "redis://localhost:6379/0"
    use_redis: bool = False

    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "169.254.169.254", "::1"]
    )

    max_agent_steps: int = 20
    max_tool_retries: int = 2
    agent_step_timeout_seconds: float = 60.0
    rate_limit: str = "60/minute"

    @field_validator("allowed_domains", "blocked_domains", mode="before")
    @classmethod
    def parse_csv_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return [item.lower() for item in value]


@lru_cache
def get_settings() -> Settings:
    return Settings()
