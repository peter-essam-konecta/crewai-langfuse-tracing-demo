"""Add Langfuse's V3 cost field to the canonical LiteLLM generation.

LiteLLM calculates ``response_cost`` from the provider response. This startup
hook exposes that same value as ``gen_ai.usage.cost`` before telemetry is sent
to Langfuse Cloud. It does not create a second model call, callback, or cost.
"""

from __future__ import annotations

from typing import Any


def install() -> None:
    """Install the V3 cost field in LiteLLM's existing generation mapper."""

    from litellm.integrations.otel.mappers.genai import GenAIMapper

    GenAIMapper._LLM_CALL_ATTRS.setdefault(
        "gen_ai.usage.cost", lambda data: _response_cost(data)
    )


def _response_cost(data: Any) -> float | None:
    """Return LiteLLM's numeric response cost, when it is available."""

    cost = getattr(data, "response_cost", None)
    if cost is None:
        return None
    try:
        return float(cost)
    except (TypeError, ValueError):
        return None
