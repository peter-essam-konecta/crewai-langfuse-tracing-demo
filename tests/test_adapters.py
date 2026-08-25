"""Unit tests for the aligned FailureAdapter and CompositeToolAdapter."""

import unittest
from types import SimpleNamespace

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind

from openlit._config import OpenlitConfig
from openlit.instrumentation.crewai.crewai import general_wrap

from crewai_langfuse_demo.adapters.composite_tool import CompositeToolAdapter
from crewai_langfuse_demo.adapters.failure import FailureAdapter


class AdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory_exporter = InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.memory_exporter))

    def test_composite_tool_adapter_creates_standard_tool_span(self) -> None:
        tracer = self.provider.get_tracer("test-tracer")
        adapter = CompositeToolAdapter(tracer=tracer)
        result = adapter.run_child(
            parent_tool="resolve_order_exception",
            child_operation="lookup_order_status",
            operation=lambda: "order_status_ok",
        )
        self.assertEqual(result, "order_status_ok")

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "execute_tool lookup_order_status")
        self.assertEqual(span.kind, SpanKind.INTERNAL)
        self.assertEqual(span.attributes.get("gen_ai.operation.name"), "execute_tool")
        self.assertEqual(span.attributes.get("gen_ai.tool.name"), "lookup_order_status")
        self.assertEqual(
            span.attributes.get("kolibri.composite.parent.tool.name"),
            "resolve_order_exception",
        )
        self.assertEqual(
            span.attributes.get("kolibri.composite.child.operation.name"),
            "lookup_order_status",
        )
        self.assertEqual(
            span.attributes.get("kolibri.composite.child.final.outcome"),
            "succeeded",
        )

    def test_openlit_crewai_tool_wrapper_uses_internal_span_kind(self) -> None:
        """Exercise OpenLIT's actual CrewAI wrapper without a model or network call."""

        OpenlitConfig()
        tracer = self.provider.get_tracer("openlit-span-kind-test")
        wrapper = general_wrap(
            "tool_run",
            "1.44.0",
            "test",
            "span-kind-test",
            tracer,
            {},
            False,
            {},
            True,
        )
        tool = SimpleNamespace(name="lookup_order_status", description="safe test tool")
        result = wrapper(lambda *args, **kwargs: "ok", tool, (), {})

        self.assertEqual(result, "ok")
        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.kind, SpanKind.INTERNAL)
        self.assertEqual(span.attributes.get("gen_ai.operation.name"), "execute_tool")
        self.assertEqual(span.attributes.get("gen_ai.tool.name"), "lookup_order_status")

    def test_failure_adapter_safe_error_type_mapping(self) -> None:
        self.assertEqual(
            FailureAdapter._safe_error_type("tool_a", TimeoutError("timed out")),
            "timeout",
        )
        self.assertEqual(
            FailureAdapter._safe_error_type("tool_a", ConnectionError("connection reset")),
            "dependency_unavailable",
        )
        self.assertEqual(
            FailureAdapter._safe_error_type("tool_a", ValueError("invalid argument")),
            "invalid_tool_input",
        )
        self.assertEqual(
            FailureAdapter._safe_error_type("tool_a", RuntimeError("general failure")),
            "tool_execution_failed",
        )
