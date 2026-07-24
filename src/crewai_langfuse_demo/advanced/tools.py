"""Safe deterministic tools used only by the advanced examples."""

from __future__ import annotations

from crewai.tools import tool

from ..adapters.composite_tool import CompositeToolAdapter

_retry_attempts = 0
_composite_adapter: CompositeToolAdapter | None = None


def reset_retry_state() -> None:
    global _retry_attempts
    _retry_attempts = 0


def retry_attempt_count() -> int:
    return _retry_attempts


def configure_composite_adapter(adapter: CompositeToolAdapter | None) -> None:
    global _composite_adapter
    _composite_adapter = adapter


@tool("lookup_retryable_order_status")
def lookup_retryable_order_status(order_id: str) -> str:
    """Fail twice safely, then succeed on the third attempt."""

    global _retry_attempts
    _retry_attempts += 1
    if _retry_attempts <= 2:
        raise RuntimeError("TEST_ONLY temporary order-status dependency failure")
    if order_id != "KOL-RETRY-123":
        return "Order not found in the safe demo data."
    return "Order KOL-RETRY-123 is delayed by one day. The safe retry succeeded."


@tool("lookup_exception_policy")
def lookup_exception_policy(exception_type: str) -> str:
    """Return the policy used in the delegation example."""

    if exception_type.lower() != "carrier delay":
        return "No matching safe policy was found."
    return "Give a delivery update and offer a safe service-credit review."


@tool("lookup_order_status_for_exception")
def lookup_order_status_for_exception(order_id: str) -> str:
    """First child operation inside the composite parent tool."""

    if order_id != "KOL-COMPOSITE-456":
        return "Order not found in the safe demo data."
    return "Order KOL-COMPOSITE-456 has a one-day carrier delay."


@tool("lookup_policy_for_exception")
def lookup_policy_for_exception(exception_type: str) -> str:
    """Second child operation inside the composite parent tool."""

    if exception_type.lower() != "carrier delay":
        return "No matching safe policy was found."
    return "Provide a delivery update and offer a safe service-credit review."


@tool("resolve_order_exception")
def resolve_order_exception(order_id: str) -> str:
    """A parent tool that calls two internal child operations."""

    status = _run_child(
        "lookup_order_status_for_exception",
        lambda: lookup_order_status_for_exception.run(order_id),
    )
    policy = _run_child(
        "lookup_policy_for_exception",
        lambda: lookup_policy_for_exception.run("carrier delay"),
    )
    return f"Safe combined result: {status} {policy}"


def _run_child(name: str, operation: object) -> object:
    if _composite_adapter is None:
        return operation()  # type: ignore[operator]
    return _composite_adapter.run_child(
        parent_tool="resolve_order_exception",
        child_operation=name,
        operation=operation,  # type: ignore[arg-type]
    )

