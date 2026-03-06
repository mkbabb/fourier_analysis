"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017/fourier"
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_upload_mb: int = 10
    session_ttl_days: int = 30

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
