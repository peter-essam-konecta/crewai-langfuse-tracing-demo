"""Unit tests for the local fictional tools; no model or Langfuse key is needed."""

import unittest

from crewai_langfuse_demo.advanced.tools import (
    lookup_exception_policy,
    lookup_order_status_for_exception,
    lookup_retryable_order_status,
    reset_retry_state,
)
from crewai_langfuse_demo.basic.tools import get_refund_policy, lookup_order_status


class ToolTests(unittest.TestCase):
    def test_basic_order_tool_uses_fictional_data(self) -> None:
        self.assertIn("delayed", lookup_order_status.run(order_id="KOL-123"))

    def test_basic_policy_tool_uses_fictional_data(self) -> None:
        self.assertIn("human", get_refund_policy.run(region="Egypt"))

    def test_retry_tool_succeeds_after_two_safe_failures(self) -> None:
        reset_retry_state()
        with self.assertRaises(RuntimeError):
            lookup_retryable_order_status.run(order_id="KOL-RETRY-123")
        with self.assertRaises(RuntimeError):
            lookup_retryable_order_status.run(order_id="KOL-RETRY-123")
        self.assertIn("succeeded", lookup_retryable_order_status.run(order_id="KOL-RETRY-123"))

    def test_advanced_tools_return_safe_static_results(self) -> None:
        self.assertIn("delivery update", lookup_exception_policy.run(exception_type="carrier delay"))
        self.assertIn("one-day", lookup_order_status_for_exception.run(order_id="KOL-COMPOSITE-456"))

