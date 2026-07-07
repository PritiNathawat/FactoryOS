"""
FactoryOS Application Configuration
====================================
All configuration is sourced from environment variables, with `.env` file support.

Pydantic Settings guarantees:
  - Type validation for every value
  - Clear startup errors when required values are missing or malformed
  - A single import (`from app.core.config import settings`) used everywhere

Never access `os.environ` directly in application code.
Always use `settings.*` instead.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings resolved from environment variables.

    Priority order (highest to lowest):
      1. Actual environment variables
      2. Variables defined in the .env file
      3. Default values defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Ignore unknown env vars — cloud environments inject many variables
        # that are not FactoryOS-specific. Crashing on them would be wrong.
        extra="ignore",
    )

    # ─── Application Identity ──────────────────────────────────
    app_name: str = "FactoryOS"
    app_version: str = "0.1.0"

    # Literal type enforced by Pydantic — invalid values are rejected at startup.
    environment: Literal["development", "staging", "production"] = "development"

    # Debug mode enables extra logging and disables some production safeguards.
    # Must NEVER be True in production.
    debug: bool = False

    # ─── API Configuration ────────────────────────────────────
    api_v1_prefix: str = "/api/v1"

    # ─── Database ────────────────────────────────────────────
    # Default: async SQLite for development (zero infrastructure required).
    # For PostgreSQL: DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/factoryos
    #
    # The `+aiosqlite` and `+asyncpg` URL schemes select the async driver.
    # SQLAlchemy 2.0's async session works identically across both drivers —
    # switching databases only requires changing this URL.
    database_url: str = "sqlite+aiosqlite:///./factoryos.db"

    # ─── CORS Configuration ───────────────────────────────────
    # During development, Next.js proxies /api/* to the backend, so CORS
    # is only needed for direct API access (Swagger UI, curl, etc.).
    # In production, set this to your actual frontend domain(s).
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
    )

    # ─── Logging ─────────────────────────────────────────────
    log_level: str = "INFO"

    # ─── AI Platform (Gemini) ────────────────────────────────
    # Set GEMINI_API_KEY in your .env file.
    # Obtain from: https://aistudio.google.com/app/apikey
    #
    # When not set, AI Platform operates in MOCK MODE —
    # all agent responses are realistic pre-defined data.
    # This allows the system to be tested without API credentials.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.3
    gemini_max_tokens: int = 2048

    # Master switch for the AI platform.
    # Set AI_PLATFORM_ENABLED=false to return 503 from analysis endpoints.
    ai_platform_enabled: bool = True

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        """Validate and normalize log level to uppercase."""
        level = str(v).upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level not in valid_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL='{v}'. Must be one of: {', '.join(sorted(valid_levels))}"
            )
        return level

    # ─── Computed Properties ──────────────────────────────────

    @property
    def is_development(self) -> bool:
        """True when running in local development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """True when running in a production environment."""
        return self.environment == "production"

    @property
    def is_sqlite(self) -> bool:
        """True when the configured database is SQLite."""
        return self.database_url.startswith("sqlite")


# ─── Module-level singleton ───────────────────────────────────
# Instantiated once when first imported. All application code imports this:
#   from app.core.config import settings
#
# This pattern ensures configuration is loaded and validated exactly once,
# at startup, rather than on every request.
settings = Settings()
