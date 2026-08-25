"""Regression tests for Final-Trace-Schema-first trace validation."""

from __future__ import annotations

import unittest

from crewai_langfuse_demo.trace_validation import detect_tools, validate_trace


TRACE_ID = "1234567890abcdef1234567890abcdef"


def observation(
    name: str,
    attributes: dict,
    *,
    observation_type: str = "SPAN",
    parent: str | None = "root",
    level: str = "DEFAULT",
    span_kind: str | None = None,
) -> dict:
    result = {
        "name": name,
        "type": observation_type,
        "parentObservationId": parent,
        "level": level,
        "metadata": {"attributes": attributes},
    }
    if span_kind:
        result["spanKind"] = span_kind
    return result


def complete_final_schema_trace(*, include_span_kind: bool = False) -> tuple[dict, list[dict]]:
    root = observation(
        "invoke_workflow Customer Support - Retry & Recovery",
        {
            "gen_ai.operation.name": "invoke_workflow",
            "gen_ai.agent.id": "crew_customer_support_01",
            "kolibri.tenant.id": "demo-workspace",
            "kolibri.channel": "chat",
            "kolibri.runtime.name": "crewai",
            "gen_ai.conversation.id": "demo-session-001",
        },
        parent=None,
    )
    agent = observation(
        "invoke_agent Retry-aware order specialist",
        {
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "Retry-aware order specialist",
        },
    )
    tool = observation(
        "execute_tool lookup_retryable_order_status",
        {
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "lookup_retryable_order_status",
        },
        span_kind="INTERNAL" if include_span_kind else None,
    )
    generation = observation(
        "chat approved-model",
        {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "gcp.gemini",
            "gen_ai.request.model": "approved-model",
            "gen_ai.response.model": "approved-model-001",
            "gen_ai.usage.input_tokens": 10,
            "gen_ai.usage.output_tokens": 4,
            "gen_ai.response.finish_reasons": ["stop"],
        },
        observation_type="GENERATION",
        span_kind="CLIENT" if include_span_kind else None,
    )
    failure_summary = observation(
        "kolibri.crewai.failure_summary",
        {
            "kolibri.failure.tool.name": "lookup_retryable_order_status",
            "error.type": "controlled_test_failure",
            "kolibri.failure.error.type": "controlled_test_failure",
            "kolibri.failure.retry.count": 1,
            "kolibri.failure.final.outcome": "retry_succeeded",
        },
        level="ERROR",
    )
    return {"id": TRACE_ID, "name": root["name"]}, [
        root,
        agent,
        tool,
        generation,
        failure_summary,
    ]


class TraceValidationTests(unittest.TestCase):
    def test_final_schema_tool_observation_is_detected(self) -> None:
        tools = detect_tools(
            [
                observation(
                    "execute_tool lookup_order_status",
                    {
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "lookup_order_status",
                    },
                )
            ]
        )
        self.assertEqual(tools["final_schema"], ["lookup_order_status"])
        self.assertEqual(tools["detected"], ["lookup_order_status"])
        self.assertEqual(tools["legacy_fallback"], [])

    def test_legacy_tool_fallback_remains_detectable(self) -> None:
        tools = detect_tools(
            [observation("Tool Usage", {"tool_name": "lookup_order_status"})],
            allow_legacy_fallback=True,
        )
        self.assertEqual(tools["detected"], ["lookup_order_status"])
        self.assertEqual(tools["legacy_fallback"], ["lookup_order_status"])
        self.assertEqual(tools["final_schema"], [])

        trace, observations = complete_final_schema_trace()
        observations[2] = observation(
            "Tool Usage", {"tool_name": "lookup_retryable_order_status"}
        )
        report = validate_trace(
            trace,
            observations,
            requested_trace_id=TRACE_ID,
            expected_tools=["lookup_retryable_order_status"],
            require_failure_summary=True,
        )
        checks = {check["id"]: check for check in report["validation"]["checks"]}
        self.assertTrue(checks["tools_detected"]["passed"])
        self.assertFalse(checks["tool_schema"]["passed"])

    def test_missing_required_tool_information_fails_validation(self) -> None:
        trace, observations = complete_final_schema_trace()
        observations[2] = observation(
            "execute_tool lookup_retryable_order_status",
            {"gen_ai.operation.name": "execute_tool"},
        )
        report = validate_trace(
            trace,
            observations,
            requested_trace_id=TRACE_ID,
            expected_tools=["lookup_retryable_order_status"],
            require_failure_summary=True,
        )
        checks = {check["id"]: check for check in report["validation"]["checks"]}
        self.assertFalse(checks["tools_detected"]["passed"])
        self.assertFalse(checks["tool_schema"]["passed"])
        self.assertEqual(
            report["tools"]["incomplete"][0]["reason"],
            "missing gen_ai.tool.name",
        )

    def test_complete_final_schema_retry_fixture_passes_eleven_checks(self) -> None:
        trace, observations = complete_final_schema_trace()
        report = validate_trace(
            trace,
            observations,
            requested_trace_id=TRACE_ID,
            expected_tools=["lookup_retryable_order_status"],
            require_failure_summary=True,
        )
        self.assertTrue(report["validation"]["passed"])
        self.assertEqual(report["validation"]["passed_count"], 11)
        self.assertEqual(report["validation"]["total_count"], 11)
        self.assertEqual(report["validation"]["coverage_percent"], 100.0)

    def test_span_kind_is_verified_only_when_exposed(self) -> None:
        trace, observations = complete_final_schema_trace(include_span_kind=True)
        report = validate_trace(trace, observations, requested_trace_id=TRACE_ID)
        self.assertEqual(
            report["span_kind"]["canonical_generations"]["status"], "verified"
        )
        self.assertEqual(report["span_kind"]["canonical_tools"]["status"], "verified")

        trace, observations = complete_final_schema_trace(include_span_kind=False)
        report = validate_trace(trace, observations, requested_trace_id=TRACE_ID)
        self.assertEqual(
            report["span_kind"]["canonical_generations"]["status"], "not_exposed"
        )
        self.assertEqual(
            report["span_kind"]["canonical_tools"]["status"], "not_exposed"
        )

    def test_transport_generation_is_not_counted_as_a_model_generation(self) -> None:
        trace, observations = complete_final_schema_trace()
        observations.append(
            observation(
                "POST /v1/chat/completions",
                {},
                observation_type="GENERATION",
            )
        )
        report = validate_trace(trace, observations, requested_trace_id=TRACE_ID)
        self.assertEqual(report["canonical_generation_count"], 1)


if __name__ == "__main__":
    unittest.main()
