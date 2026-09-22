"""
Application configuration.

Loads settings from environment variables (and a local .env file during
development) into a single typed, validated object. No other module in
this app should call os.environ or os.getenv directly — everything goes
through this Settings object so config stays centralized and predictable.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Groq API credentials
    groq_api_key: str

    # LLM behavior defaults
    default_model: str = "openai/gpt-oss-120b"
    llm_timeout: int = 30  # seconds

    # Logging
    log_level: str = "INFO"

    # Tells pydantic-settings where to load values from and how to match
    # env var names (case-insensitive) to these field names.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# A single shared instance, imported everywhere else in the app.
# e.g.  from app.core.config import settings
settings = Settings()