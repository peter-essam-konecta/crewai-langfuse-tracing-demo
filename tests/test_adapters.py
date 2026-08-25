"""Unit tests for the aligned FailureAdapter and CompositeToolAdapter."""

import unittest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

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
