from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path so settings load correctly regardless of the process's CWD
# (e.g. scripts/ run from the repo root rather than from backend/).
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    environment: str = "development"

    database_url: str = "postgresql+psycopg://uniride:uniride_dev_password@localhost:5432/uniride"

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24

    google_maps_api_key: str | None = None

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
