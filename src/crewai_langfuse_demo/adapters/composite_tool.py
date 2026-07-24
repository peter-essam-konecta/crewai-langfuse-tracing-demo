"""An opt-in adapter for important child operations inside one parent tool."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

Result = TypeVar("Result")


class CompositeToolAdapter:
    """Add only the child operation that automatic tracing cannot see."""

    def run_child(
        self,
        *,
        parent_tool: str,
        child_operation: str,
        operation: Callable[[], Result],
    ) -> Result:
        tracer = trace.get_tracer("crewai-langfuse-demo.composite-adapter")
        with tracer.start_as_current_span(f"demo.composite.child.{child_operation}") as span:
            span.set_attribute("demo.composite.parent.tool.name", parent_tool)
            span.set_attribute("demo.composite.child.operation.name", child_operation)
            try:
                result = operation()
            except Exception:
                span.set_attribute("demo.composite.child.final.outcome", "failed")
                span.set_status(Status(StatusCode.ERROR, "safe child-operation failure"))
                raise
            span.set_attribute("demo.composite.child.final.outcome", "succeeded")
            return result

