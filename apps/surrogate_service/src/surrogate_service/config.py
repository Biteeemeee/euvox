from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://euvox:euvox@localhost:5432/euvox"
    broker_url: str = "amqp://euvox:euvox@localhost:5672/"
    surrogate_model_dir: str = "/tmp/euvox_surrogates"
    min_samples_to_train: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
