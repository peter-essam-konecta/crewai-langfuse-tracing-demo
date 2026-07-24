"""A safe, reusable summary for a CrewAI tool failure and its final outcome."""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan, SpanContext, Status, StatusCode


@dataclass(frozen=True)
class FailureRecord:
    tool_name: str
    error_type: str
    retry_count: int
    parent_context: SpanContext | None


class FailureAdapter:
    """Listen to existing CrewAI events and add one safe summary per failed tool.

    This does not replace automatic tracing and does not inspect arguments,
    prompts, responses, raw errors, or stack traces.
    """

    def __init__(self) -> None:
        self._failure_counts: dict[str, int] = defaultdict(int)
        self._start_counts: dict[str, int] = defaultdict(int)
        self._finished_tools: set[str] = set()
        self._records: dict[str, FailureRecord] = {}
        self._registrations: list[tuple[type[Any], Any]] = []

    def install(self) -> None:
        """Register beside CrewAI's own event handlers for one crew run."""

        from crewai.events.event_bus import crewai_event_bus
        from crewai.events.types.tool_usage_events import (
            ToolUsageErrorEvent,
            ToolUsageFinishedEvent,
            ToolUsageStartedEvent,
        )

        crewai_event_bus.register_handler(ToolUsageStartedEvent, self._on_started)
        crewai_event_bus.register_handler(ToolUsageErrorEvent, self._on_error)
        crewai_event_bus.register_handler(ToolUsageFinishedEvent, self._on_finished)
        self._registrations = [
            (ToolUsageStartedEvent, self._on_started),
            (ToolUsageErrorEvent, self._on_error),
            (ToolUsageFinishedEvent, self._on_finished),
        ]

    def complete(self, *, crew_completed: bool) -> None:
        """Write one safe summary after the crew has finished."""

        tracer = trace.get_tracer("crewai-langfuse-demo.failure-adapter")
        for record in self._records.values():
            retry_count = max(record.retry_count, self._start_counts[record.tool_name] - 1)
            parent = self._parent_context(record.parent_context)
            with tracer.start_as_current_span("demo.failure_summary", context=parent) as span:
                span.set_attribute("demo.failure.tool.name", record.tool_name)
                span.set_attribute("demo.failure.error.type", record.error_type)
                span.set_attribute("demo.failure.retry.count", retry_count)
                span.set_attribute(
                    "demo.failure.final.outcome",
                    self._outcome(record.tool_name, crew_completed),
                )
                span.set_status(Status(StatusCode.ERROR, "safe tool failure"))

    def uninstall(self) -> None:
        """Remove this adapter's listeners after the example run."""

        if not self._registrations:
            return
        from crewai.events.event_bus import crewai_event_bus

        for event_type, handler in self._registrations:
            crewai_event_bus.off(event_type, handler)
        self._registrations.clear()

    def _on_started(self, source: Any, event: Any) -> None:
        self._start_counts[str(getattr(event, "tool_name", "unknown"))] += 1

    def _on_finished(self, source: Any, event: Any) -> None:
        self._finished_tools.add(str(getattr(event, "tool_name", "unknown")))

    def _on_error(self, source: Any, event: Any) -> None:
        tool_name = str(getattr(event, "tool_name", "unknown"))
        self._failure_counts[tool_name] += 1
        current_context = trace.get_current_span().get_span_context()
        self._records[tool_name] = FailureRecord(
            tool_name=tool_name,
            error_type=self._safe_error_type(tool_name, getattr(event, "error", None)),
            retry_count=self._failure_counts[tool_name] - 1,
            parent_context=current_context if current_context.is_valid else None,
        )

    @staticmethod
    def _safe_error_type(tool_name: str, error: Any) -> str:
        if os.getenv("DEMO_RETRY_TEST", "") == tool_name:
            return "controlled_test_failure"
        if isinstance(error, TimeoutError):
            return "timeout"
        if isinstance(error, ConnectionError):
            return "dependency_unavailable"
        if isinstance(error, ValueError):
            return "invalid_tool_input"
        return "tool_execution_failed"

    def _outcome(self, tool_name: str, crew_completed: bool) -> str:
        if not crew_completed:
            return "aborted"
        if tool_name in self._finished_tools:
            return "retry_succeeded"
        return "fallback_completed"

    @staticmethod
    def _parent_context(span_context: SpanContext | None) -> Any | None:
        if span_context is None:
            return None
        return trace.set_span_in_context(NonRecordingSpan(span_context))

