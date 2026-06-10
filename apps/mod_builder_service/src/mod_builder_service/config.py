from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://euvox:euvox@localhost:5432/euvox"
    broker_url: str = "amqp://euvox:euvox@localhost:5672/"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "euvox"
    minio_secret_key: str = "euvoxsecret"
    artifact_bucket: str = "euvox-artifacts"
    use_local_store: bool = False
    local_store_dir: str = "./artifacts"


@lru_cache
def get_settings() -> Settings:
    return Settings()
