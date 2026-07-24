"""Load local settings without printing secret values."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    langfuse_base_url: str
    langfuse_public_key: str
    langfuse_secret_key: str
    litellm_proxy_host: str
    litellm_master_key: str
    service_name: str
    tenant_id: str
    conversation_id: str


def load_settings() -> Settings:
    """Read .env from the repository root and require the needed secrets."""

    repository_root = Path(__file__).resolve().parents[2]
    env_path = repository_root / ".env"
    if not env_path.exists():
        raise FileNotFoundError("Missing .env. Copy .env.example to .env first.")

    load_dotenv(env_path, override=False)

    def required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"{name} is missing from .env.")
        return value

    return Settings(
        langfuse_base_url=os.getenv("LANGFUSE_BASE_URL", "http://localhost:3000").rstrip("/"),
        langfuse_public_key=required("LANGFUSE_PUBLIC_KEY"),
        langfuse_secret_key=required("LANGFUSE_SECRET_KEY"),
        litellm_proxy_host=os.getenv("LITELLM_PROXY_HOST", "http://localhost:4000").rstrip("/"),
        litellm_master_key=required("LITELLM_MASTER_KEY"),
        service_name=os.getenv("OTEL_SERVICE_NAME", "crewai-langfuse-tracing-demo"),
        tenant_id=os.getenv("DEMO_TENANT_ID", "demo-workspace"),
        conversation_id=os.getenv("DEMO_CONVERSATION_ID", "demo-session-001"),
    )

