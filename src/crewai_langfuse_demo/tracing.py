"""One automatic CrewAI tracing setup for every example in this repository."""

from __future__ import annotations

import base64
import os
from collections.abc import MutableMapping

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config import Settings


class SchemaV3SpanProcessor(SpanProcessor):
    """Normalize and redact automatic spans before any exporter sees them."""

    def _on_ending(self, span) -> None:  # type: ignore[no-untyped-def]
        attributes = getattr(span, "_attributes", None)
        if not isinstance(attributes, MutableMapping):
            return

        cost = attributes.get("litellm.cost.total")
        if cost is not None:
            try:
                attributes["gen_ai.usage.cost"] = float(cost)
            except (ValueError, TypeError):
                pass


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

    authorization = base64.b64encode(
        f"{settings.langfuse_public_key}:{settings.langfuse_secret_key}".encode("ascii")
    ).decode("ascii")
    headers = {
        "Authorization": f"Basic {authorization}",
        "x-langfuse-ingestion-version": "4",
    }
    otlp_endpoint = f"{settings.langfuse_base_url}/api/public/otel"

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": settings.service_name,
                "deployment.environment.name": "development",
                "kolibri.schema.version": "3.0",
            }
        )
    )
    provider.add_span_processor(SchemaV3SpanProcessor())
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces", headers=headers)
        )
    )
    trace.set_tracer_provider(provider)

    import openlit

    openlit.init(
        environment="development",
        service_name=settings.service_name,
        otlp_endpoint=otlp_endpoint,
        otlp_headers=headers,
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

    # CrewAI/LiteLLM use HTTPX or aiohttp to call the Proxy. These automatic
    # instrumentors forward the current trace context so the Proxy's canonical
    # generation joins the CrewAI workflow instead of becoming a separate
    # trace. They do not create application-owned spans.
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    AioHttpClientInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()


def flush_tracing() -> None:
    """Send pending telemetry before a short command-line run exits."""

    force_flush = getattr(trace.get_tracer_provider(), "force_flush", None)
    if callable(force_flush):
        force_flush(timeout_millis=10_000)
