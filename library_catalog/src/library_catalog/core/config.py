"""
Конфигурация приложения.

Загружает настройки из переменных окружения и .env файла.
"""

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.
    
    Загружаются из переменных окружения и .env файла.
    """
    
    # Application
    app_name: str = "Library Catalog API"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    
    # Database
    database_url: PostgresDsn
    database_pool_size: int = 20
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    # Documentation
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: list[str] = ["*"]
    
    # Open Library API
    openlibrary_base_url: str = "https://openlibrary.org"
    openlibrary_timeout: float = 10.0
    
    # Cache
    cache_backend: Literal["memory", "redis"] = "memory"
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 300  # 5 минут
    
    # JWT Authentication
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60  # Общий лимит по умолчанию
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    @property
    def is_production(self) -> bool:
        """Проверить, работает ли приложение в production."""
        return self.environment == "production"
    
    @property
    def database_url_str(self) -> str:
        """Получить DATABASE_URL как строку."""
        return str(self.database_url)
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Парсить CORS origins из строки JSON или списка."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Получить настройки приложения (singleton).
    
    Использует lru_cache для кэширования экземпляра.
    """
    return Settings()


# Глобальный экземпляр настроек
settings = get_settings()

