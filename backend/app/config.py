from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "SupportOps Agent"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./supportops.db")
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    cors_origins: tuple[str, ...] = (
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    )


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./supportops.db"),
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
