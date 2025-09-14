from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/postgres"

    GOOGLE_CLIENT_ID: str = Field(...)
    GOOGLE_CLIENT_SECRET: str = Field(...)
    OAUTH_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # Poller
    POLL_INTERVAL_SECONDS: int = 60

    # LLM for answering
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = Field(...)
    LLM_FALLBACK_PROVIDER: str | None = "openrouter"

    # OpenRouter (OpenAI-compatible) settings
    OPENROUTER_API_KEY: str = Field(...)
    OPENROUTER_SITE_URL: str = Field(...)
    OPENROUTER_APP_NAME: str = Field(
        ...,
        description="App name (e.g. 'Support Email Agent')",
    )
    FRONTEND_URL: str = Field(
        ..., description="Frontend base URL, e.g. http://localhost:5173"
    )
    EMBED_DIM: int = 384

    EMBEDDING_PROVIDER: str = "openai"  # "openai" or "openrouter"
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # 1536 dims
    EMBEDDING_FALLBACK_PROVIDER: str | None = "openrouter"

    # Application base URL (for email links, etc)
    APP_BASE_URL: str = "http://localhost:8000"


settings = Settings()
