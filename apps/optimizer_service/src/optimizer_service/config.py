from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://euvox:euvox@localhost:5432/euvox"
    broker_url: str = "amqp://euvox:euvox@localhost:5672/"
    game_version: str = "1.0.0"
    default_start_date: str = "1444.11.11"
    default_end_date: str = "1450.01.01"
    evolutionary_threshold: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
