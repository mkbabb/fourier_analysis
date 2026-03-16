"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017/fourier"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_upload_mb: int = 10
    compute_timeout_s: int = 300
    compute_concurrency: int = 4
    asset_max_age_days: int = 30
    storage_budget_gb: float = 5.0
    admin_token: str = ""
    gallery_page_size: int = 20
    session_ttl_days: int = 7
    user_max_age_days: int = 90

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()


def get_settings() -> Settings:
    return settings
