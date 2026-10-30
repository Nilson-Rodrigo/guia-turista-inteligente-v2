from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do backend carregadas do ambiente ou de .env."""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    google_client_id: str = ""
    cors_origins: str = "http://localhost:5173"
    app_name: str = "Guia do Turista Inteligente API"
    app_version: str = "2.0.0"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        configured = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        local_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ]
        return list(dict.fromkeys([*configured, *local_origins]))


@lru_cache
def get_settings() -> Settings:
    return Settings()
