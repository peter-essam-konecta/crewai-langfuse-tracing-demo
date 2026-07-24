"""One automatic CrewAI tracing setup for every example in this repository."""

from __future__ import annotations

import base64
import os

from .config import Settings


def configure_tracing(settings: Settings) -> None:
    """Start OpenLIT before importing CrewAI.

    This function creates no crew, agent, task, or tool spans. OpenLIT creates
    those observations automatically. The LiteLLM Proxy remains the source of
    canonical model-call telemetry.
    """

    os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_base_url)
    os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "no_content")
    os.environ.setdefault("OTEL_SERVICE_NAME", settings.service_name)
    os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

    import openlit

    authorization = base64.b64encode(
        f"{settings.langfuse_public_key}:{settings.langfuse_secret_key}".encode("ascii")
    ).decode("ascii")
    openlit.init(
        environment="development",
        service_name=settings.service_name,
        otlp_endpoint=f"{settings.langfuse_base_url}/api/public/otel",
        otlp_headers={
            "Authorization": f"Basic {authorization}",
            "x-langfuse-ingestion-version": "4",
        },
        disable_metrics=True,
        disable_events=True,
        capture_message_content=False,
        # The Proxy already produces the model-generation telemetry. Disabling
        # these client instrumentors avoids duplicate model observations.
        disabled_instrumentors=["litellm", "openai"],
        custom_span_attributes={
            "demo.tenant.id": settings.tenant_id,
            "demo.conversation.id": settings.conversation_id,
            "demo.runtime": "crewai",
        },
    )


def flush_tracing() -> None:
    """Send pending telemetry before a short command-line run exits."""

    from opentelemetry import trace

    force_flush = getattr(trace.get_tracer_provider(), "force_flush", None)
    if callable(force_flush):
        force_flush(timeout_millis=10_000)

