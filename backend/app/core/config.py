from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path so settings load correctly regardless of the process's CWD
# (e.g. scripts/ run from the repo root rather than from backend/).
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

DEFAULT_SECRET_KEY = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    environment: str = "development"

    database_url: str = "postgresql+psycopg://uniride:uniride_dev_password@localhost:5432/uniride"

    secret_key: str = DEFAULT_SECRET_KEY
    access_token_expire_minutes: int = 60 * 24

    google_maps_api_key: str | None = None

    cors_origins: list[str] = ["http://localhost:5173"]

    @model_validator(mode="after")
    def _forbid_default_secret_in_production(self) -> "Settings":
        if self.environment == "production" and self.secret_key == DEFAULT_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be set to a real value when ENVIRONMENT=production "
                "(generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
            )
        return self


settings = Settings()
