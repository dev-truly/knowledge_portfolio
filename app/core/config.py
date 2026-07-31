from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Slack Web Agent"
    app_env: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: str = "DEBUG"

    host: str = "0.0.0.0"
    port: int = 8000

    openai_api_key: str = Field(min_length=1)
    openai_api_base: str | None = None
    openai_model: str = "gpt-4.1-mini"
    local_embedding_model: str = "model/embedding-20250715"
    # openai_temperature: float = 0

    slack_app_token: str = Field(
        min_length=1,
        description="xapp-로 시작하는 Socket Mode App Token",
    )
    slack_bot_token: str = Field(
        min_length=1,
        description="xoxb-로 시작하는 Bot User OAuth Token",
    )

    # Document & VectorStore Settings
    o_s_host: str = "localhost"
    o_s_port: int = 9200
    o_s_user: str = "admin"
    o_s_pass: str = "admin"
    o_s_use_ssl: bool = False
    o_s_document_index: str = "parent_child_chunk_index"
    
    split_chunk_size: int = 200
    split_chunk_overlap: int = 20
    persist_directory: str = "data/vectorstore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()