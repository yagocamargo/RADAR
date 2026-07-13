from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Radar"
    ENV: str = "development"

    SECRET_KEY: str = "change-me"
    JWT_SECRET_KEY: str = "change-me-too"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    POSTGRES_DB: str = "radar"
    POSTGRES_USER: str = "radar"
    POSTGRES_PASSWORD: str = "radar_secret"
    DATABASE_URL: str = "postgresql+asyncpg://radar:radar_secret@postgres:5432/radar"

    REDIS_PASSWORD: str = "redis_secret"
    REDIS_URL: str = "redis://:redis_secret@redis:6379/0"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_TEXT_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    PNCP_BASE_URL: str = "https://pncp.gov.br/api/pncp/v1"
    RECEITAWS_URL: str = "https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    BRASILAPI_URL: str = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:80", "http://localhost"]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)


settings = Settings()
