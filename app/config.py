"""Environment-backed application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded exclusively from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    mongodb_uri: str = Field(validation_alias="MONGODB_URI")
    mongodb_db: str = Field(default="expense_claims", validation_alias="MONGODB_DB")
    secret_key: str = Field(validation_alias="SECRET_KEY")
    llm_provider: str | None = Field(default=None, validation_alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, validation_alias="LLM_API_KEY")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    max_receipt_age_days: int = 90
    amount_cap_paise: int = 5_000_000


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""

    return Settings()
