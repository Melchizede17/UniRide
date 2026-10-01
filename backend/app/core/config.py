from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    database_url: str = "postgresql+psycopg://uniride:uniride_dev_password@localhost:5432/uniride"

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24

    google_maps_api_key: str | None = None

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
