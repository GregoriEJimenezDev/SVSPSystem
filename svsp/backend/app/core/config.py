from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuracion central de la aplicacion, leida desde variables de entorno."""

    database_url: str = "postgresql://svsp_user:svsp_pass@localhost:5432/svsp_db"
    secret_key: str = "change-this-to-a-long-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    frontend_origin: str = "http://localhost:5173"
    attendance_retention_days: int = 14

    class Config:
        env_file = ".env"


settings = Settings()
