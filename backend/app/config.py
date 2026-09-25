from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://archaeologist:archaeologist@localhost:5432/archaeologist"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_hours: int = 12
    scans_per_hour: int = 10
    user_agent: str = "WebsiteArchaeologistBot/1.0 (+https://example.com/bot)"
    frontend_origin: str = "http://localhost:5173"
    max_body_bytes: int = 10 * 1024 * 1024
    max_redirects: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
