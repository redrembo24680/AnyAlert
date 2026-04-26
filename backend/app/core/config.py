from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AnyAlert API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./anyalert.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_allow_origins: str = "http://localhost:3000,http://localhost:3001"
    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    email_verification_code_ttl_minutes: int = 10
    email_enabled: bool = False
    email_from: str = "noreply@anyalert.local"
    email_from_name: str = "AnyAlert"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_starttls: bool = False
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 10

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
