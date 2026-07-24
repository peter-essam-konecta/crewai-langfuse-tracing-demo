"""Three deterministic local tools using fictional order-support data."""

from crewai.tools import tool


@tool("lookup_order_status")
def lookup_order_status(order_id: str) -> str:
    """Return a safe static result for the demo order."""

    if order_id != "KOL-123":
        return "Order not found in the safe demo data."
    return "Order KOL-123 is delayed by carrier capacity. Estimated delivery is tomorrow."


@tool("get_refund_policy")
def get_refund_policy(region: str) -> str:
    """Return a safe static policy result for the demo region."""

    if region.lower() == "egypt":
        return "Offer a shipping-fee credit after a 72-hour delay; send cancellation requests to a human."
    return "Policy is case-by-case outside the demo region."


@tool("create_response_checklist")
def create_response_checklist(issue_type: str) -> str:
    """Return a safe checklist used by the final crew task."""

    return f"For {issue_type}: acknowledge the delay, share the update, and explain the next step."

