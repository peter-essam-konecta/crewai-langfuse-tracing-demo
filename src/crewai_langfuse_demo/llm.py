"""The LiteLLM Proxy-compatible CrewAI model helper."""

from __future__ import annotations

from crewai import LLM

from .config import Settings


class ProxyCompatibleLLM(LLM):
    """Remove CrewAI's internal cache marker before the Proxy request."""

    def _format_messages_for_provider(self, messages: list[dict]) -> list[dict]:
        cleaned = [
            {key: value for key, value in message.items() if key != "cache_breakpoint"}
            for message in messages
        ]
        return super()._format_messages_for_provider(cleaned)


def create_llm(settings: Settings) -> ProxyCompatibleLLM:
    """Create the one LLM route used by all examples."""

    return ProxyCompatibleLLM(
        model="openai/demo-groq",
        base_url=f"{settings.litellm_proxy_host}/v1",
        api_key=settings.litellm_master_key,
        temperature=0,
    )

