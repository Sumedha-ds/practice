"""Application configuration module."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="APP_")

    project_name: str = "Job Management API"
    description: str = "API for managing jobs, users, and job applications"
    version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./jobs.db"
    allow_origins: List[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()


