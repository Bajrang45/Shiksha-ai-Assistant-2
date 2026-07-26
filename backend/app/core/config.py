from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Smart Education Assistant"
    environment: Literal["development", "production", "test"] = "development"
    secret_key: str = "development-only-change-this-secret-key"
    access_token_expire_minutes: int = 1440
    mongodb_uri: str | None = None
    mongodb_database: str = "shiksha_assistant"
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4.1-mini"
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
