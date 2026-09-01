from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import AliasChoices, Field, SecretStr, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "production", "test"]
ENV_FILE_NAME = ".env"


def find_env_file(start_dir: Path | None = None) -> Path | None:
    """Searches the current directory and  its parents for  a '.env' file."""

    current_dir = (start_dir or Path.cwd()).resolve()
    for directory in (current_dir, *current_dir.parents):
        env_file = directory / ENV_FILE_NAME
        if env_file.is_file():
            return env_file
    return None


class Settings(BaseSettings):
    app_name: str = "Atlas API"
    environment: Environment = "development"

    database_url: str | None = None
    db_echo: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    finnhub_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("FINNHUB_API_KEY", "finnhub_api_key"),
    )
    tickerbot_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("TICKERBOT_API_KEY", "tickerbot_api_key"),
    )
    groq_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("GROQ_API_KEY", "groq_api_key"),
    )
    ai_model: str = Field(
        default="openai/gpt-oss-120b",
        validation_alias=AliasChoices("AI_MODEL", "ai_model"),
    )
    ai_reasoning_effort: Literal["low", "medium", "high"] = Field(
        default="medium",
        validation_alias=AliasChoices("AI_REASONING_EFFORT", "ai_reasoning_effort"),
    )
    ai_max_completion_tokens: int = Field(
        default=4096,
        validation_alias=AliasChoices(
            "AI_MAX_COMPLETION_TOKENS", "ai_max_completion_tokens"
        ),
    )

    tickerbot_base_url: str = Field(
        default="https://api.tickerbot.io/v2",
        validation_alias=AliasChoices("TICKERBOT_BASE_URL", "tickerbot_base_url"),
    )

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    def __init__(self, **values: Any) -> None:

        env_file = find_env_file()
        kwargs: dict[str, Any] = {}
        if env_file is not None:
            kwargs["_env_file"] = env_file

        super().__init__(**kwargs, **values)

    @model_validator(mode="after")
    def validate_required_settings(self) -> "Settings":
        """Validates that required settings are set."""
        if self.environment != "test" and not self.finnhub_api_key:
            raise ValueError(
                "FINNHUB_API_KEY is required. Set it in .env or as an environment variable."
            )
        if self.environment != "test" and not self.tickerbot_api_key:
            raise ValueError(
                "TICKERBOT_API_KEY is required. Set it in .env or as an environment variable."
            )
        if self.environment != "test" and not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is required. Set it in .env or as an environment variable."
            )
        if self.environment == "production" and not self.database_url:
            raise ValueError(
                "DATABASE_URL is required. Set it in .env or as an environment variable."
            )
        return self

    @computed_field
    @property
    def effective_database_url(self) -> str:
        """Returns the configured database URL or the default for the environment."""
        if self.database_url:
            return self.database_url

        if self.environment == "test":
            return "postgresql+psycopg://postgres:postgres@postgres:5432/atlas_test"

        return "postgresql+psycopg://postgres:postgres@postgres:5432/atlas_dev"


@lru_cache
def get_settings() -> Settings:
    """Returns a Settings instance."""
    return Settings()
