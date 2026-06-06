import hashlib
import platform
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_fingerprint() -> str:
    raw = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    control_api_url: str = "http://localhost:8000"
    client_name: str = "simulation-client"
    client_version: str = "0.1.0"
    machine_fingerprint: str = Field(default_factory=_default_fingerprint)
    work_dir: Path = Path("./work")
    poll_interval: float = 5.0
    heartbeat_interval: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
