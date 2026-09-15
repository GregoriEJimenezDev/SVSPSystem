from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SVSP"
    app_version: str = "1.0.0"
    debug: bool = True

    database_url: str = "postgresql://user:password@localhost:5432/svsp"

    secret_key: str = "change-me-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    admin_email: str = "admin@svsp.local"
    admin_password: str = "Admin123!"
    admin_full_name: str = "Administrador SVSP"

    public_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
