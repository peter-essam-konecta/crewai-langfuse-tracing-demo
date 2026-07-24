"""The smallest safe way to show hidden child operations inside one parent tool.

Full explanation:
https://github.com/peter-essam-konecta/crewai-langfuse-tracing-demo/blob/main/docs/composite-tool-adapter-reference.md
"""

from __future__ import annotations

from crewai_langfuse_demo.adapters.composite_tool import CompositeToolAdapter


adapter = CompositeToolAdapter()


def resolve_order_exception(order_id: str) -> str:
    """A parent tool that performs two internal operations.

    Automatic CrewAI tracing shows this parent tool. The adapter makes only the
    two selected child operations visible in the same Langfuse trace.
    """

    status = adapter.run_child(
        parent_tool="resolve_order_exception",
        child_operation="lookup_order_status",
        operation=lambda: lookup_order_status(order_id),
    )
    policy = adapter.run_child(
        parent_tool="resolve_order_exception",
        child_operation="lookup_delay_policy",
        operation=lambda: lookup_delay_policy("carrier delay"),
    )
    return f"Safe combined result: {status} {policy}"


def lookup_order_status(order_id: str) -> str:
    """Replace this fictional child operation with your real internal function."""

    return f"Safe demo status for {order_id}."


def lookup_delay_policy(reason: str) -> str:
    """Replace this fictional child operation with your real internal function."""

    return f"Safe demo policy for {reason}."

