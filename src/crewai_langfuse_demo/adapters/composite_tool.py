"""An opt-in adapter for important child operations inside one parent tool."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode

Result = TypeVar("Result")


class CompositeToolAdapter:
    """Add only the child operation that automatic tracing cannot see."""

    def __init__(self, tracer: trace.Tracer | None = None) -> None:
        self._tracer = tracer

    def run_child(
        self,
        *,
        parent_tool: str,
        child_operation: str,
        operation: Callable[[], Result],
    ) -> Result:
        tracer = self._tracer or trace.get_tracer("crewai-langfuse-demo.composite-adapter")
        with tracer.start_as_current_span(
            f"execute_tool {child_operation}", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("gen_ai.operation.name", "execute_tool")
            span.set_attribute("gen_ai.tool.name", child_operation)
            span.set_attribute("kolibri.composite.parent.tool.name", parent_tool)
            span.set_attribute("kolibri.composite.child.operation.name", child_operation)
            try:
                result = operation()
            except Exception:
                span.set_attribute("kolibri.composite.child.final.outcome", "failed")
                span.set_status(Status(StatusCode.ERROR, "safe child-operation failure"))
                raise
            span.set_attribute("kolibri.composite.child.final.outcome", "succeeded")
            return result
