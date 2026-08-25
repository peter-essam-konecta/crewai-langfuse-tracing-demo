"""Schema-first, payload-safe validation for Langfuse trace API responses."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


RUN_OPERATIONS = {"invoke_agent", "invoke_workflow"}
GENERATION_OPERATIONS = {"chat", "generate_content", "text_completion"}
REQUIRED_CONTEXT_ATTRIBUTES = (
    "kolibri.tenant.id",
    "gen_ai.conversation.id",
    "gen_ai.agent.id",
    "kolibri.runtime.name",
    "kolibri.channel",
)
REQUIRED_GENERATION_ATTRIBUTES = (
    "gen_ai.provider.name",
    "gen_ai.request.model",
    "gen_ai.response.model",
    "gen_ai.usage.input_tokens",
    "gen_ai.usage.output_tokens",
    "gen_ai.response.finish_reasons",
)
REQUIRED_FAILURE_SUMMARY_ATTRIBUTES = (
    "kolibri.failure.tool.name",
    "error.type",
    "kolibri.failure.error.type",
    "kolibri.failure.retry.count",
    "kolibri.failure.final.outcome",
)
REQUIRED_COMPOSITE_ATTRIBUTES = (
    "gen_ai.operation.name",
    "gen_ai.tool.name",
    "kolibri.composite.parent.tool.name",
    "kolibri.composite.child.operation.name",
    "kolibri.composite.child.final.outcome",
)
SPAN_KIND_FIELDS = (
    "spanKind",
    "span_kind",
    "otel.span.kind",
    "span.kind",
    "opentelemetry.span.kind",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def observation_attributes(observation: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the attributes shape exposed by the Langfuse public API."""

    return _mapping(_mapping(observation.get("metadata")).get("attributes"))


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def _unique(values: Iterable[str]) -> list[str]:
    return sorted({value for value in values if value})


def detect_tools(
    observations: Sequence[Mapping[str, Any]],
    *,
    allow_legacy_fallback: bool = True,
) -> dict[str, Any]:
    """Detect tools by Final Trace Schema fields, then by an explicit fallback."""

    canonical: list[str] = []
    legacy: list[str] = []
    incomplete: list[dict[str, str]] = []

    for observation in observations:
        name = str(observation.get("name") or "")
        attributes = observation_attributes(observation)
        operation = attributes.get("gen_ai.operation.name")
        tool_name = attributes.get("gen_ai.tool.name")

        if operation == "execute_tool":
            if _present(tool_name):
                canonical.append(str(tool_name))
            else:
                incomplete.append(
                    {"observation": name or "<unnamed>", "reason": "missing gen_ai.tool.name"}
                )
            continue

        if name.startswith("execute_tool "):
            incomplete.append(
                {
                    "observation": name,
                    "reason": "missing gen_ai.operation.name=execute_tool",
                }
            )
            continue

        if name in {"Tool Usage", "Tool Usage Error"}:
            legacy_name = attributes.get("tool_name")
            if _present(legacy_name):
                legacy.append(str(legacy_name))
            else:
                incomplete.append(
                    {
                        "observation": name,
                        "reason": "legacy tool observation has no tool_name",
                    }
                )

    canonical_names = _unique(canonical)
    legacy_names = _unique(legacy)
    detected = _unique(
        canonical_names + (legacy_names if allow_legacy_fallback else [])
    )
    return {
        "detected": detected,
        "final_schema": canonical_names,
        "legacy_fallback": legacy_names,
        "incomplete": incomplete,
        "legacy_fallback_enabled": allow_legacy_fallback,
    }


def _extract_span_kind(observation: Mapping[str, Any]) -> str | None:
    attributes = observation_attributes(observation)
    metadata = _mapping(observation.get("metadata"))
    for source in (observation, metadata, attributes):
        for field in SPAN_KIND_FIELDS:
            value = source.get(field)
            if _present(value):
                normalized = str(value).strip().upper().replace("SPAN_KIND_", "")
                return normalized.replace("SPANKIND.", "")
    return None


def _span_kind_result(
    observations: Sequence[Mapping[str, Any]], expected: str
) -> dict[str, Any]:
    inspected = [
        {"name": str(observation.get("name") or "<unnamed>"), "kind": kind}
        for observation in observations
        if (kind := _extract_span_kind(observation)) is not None
    ]
    if not observations:
        return {"status": "not_applicable", "expected": expected, "inspected": []}
    if not inspected:
        return {"status": "not_exposed", "expected": expected, "inspected": []}
    mismatches = [item for item in inspected if item["kind"] != expected]
    return {
        "status": "failed" if mismatches else "verified",
        "expected": expected,
        "inspected": inspected,
        "mismatches": mismatches,
    }


def _check(check_id: str, description: str, passed: bool, detail: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "description": description,
        "passed": bool(passed),
        "detail": detail,
    }


def validate_trace(
    trace: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
    *,
    requested_trace_id: str,
    expected_tools: Sequence[str] = (),
    require_failure_summary: bool = False,
    expected_composite_children: Sequence[str] = (),
    allow_legacy_tool_fallback: bool = True,
) -> dict[str, Any]:
    """Validate the repository's checkable Final Trace Schema subset.

    The result always contains exactly eleven structural checks. SpanKind,
    privacy, cost parity, and full hierarchy are reported separately because
    the Langfuse public API cannot prove all of them.
    """

    observations = list(observations)
    workflow_candidates = [
        observation
        for observation in observations
        if observation_attributes(observation).get("gen_ai.operation.name")
        == "invoke_workflow"
    ]
    workflow_runs = [
        observation
        for observation in workflow_candidates
        if not observation.get("parentObservationId")
    ]
    if not workflow_runs:
        workflow_runs = [
            observation
            for observation in workflow_candidates
            if observation.get("name") == trace.get("name")
        ]
    if not workflow_runs and len(workflow_candidates) == 1:
        workflow_runs = workflow_candidates

    single_agent_runs = [
        observation
        for observation in observations
        if observation_attributes(observation).get("gen_ai.operation.name")
        == "invoke_agent"
        and not observation.get("parentObservationId")
    ]
    run_observations = workflow_runs or single_agent_runs
    root = run_observations[0] if len(run_observations) == 1 else {}
    root_attributes = observation_attributes(root)
    root_operation = root_attributes.get("gen_ai.operation.name")

    agents: list[str] = []
    incomplete_agents: list[str] = []
    for observation in observations:
        attributes = observation_attributes(observation)
        if attributes.get("gen_ai.operation.name") != "invoke_agent":
            continue
        name = attributes.get("gen_ai.agent.name")
        if _present(name):
            agents.append(str(name))
        else:
            incomplete_agents.append(str(observation.get("name") or "<unnamed>"))
    agents = _unique(agents)

    tools = detect_tools(
        observations, allow_legacy_fallback=allow_legacy_tool_fallback
    )
    expected_tool_set = set(expected_tools)
    detected_tool_set = set(tools["detected"])
    final_tool_set = set(tools["final_schema"])
    tool_detection_passed = bool(detected_tool_set) and expected_tool_set.issubset(
        detected_tool_set
    )
    tool_schema_passed = (
        bool(final_tool_set)
        and not tools["incomplete"]
        and expected_tool_set.issubset(final_tool_set)
        and not tools["legacy_fallback"]
    )

    generations = [
        observation
        for observation in observations
        if observation.get("type") == "GENERATION"
        and observation_attributes(observation).get("gen_ai.operation.name")
        in GENERATION_OPERATIONS
    ]
    incomplete_generations: list[dict[str, Any]] = []
    for observation in generations:
        attributes = observation_attributes(observation)
        missing = [
            field for field in REQUIRED_GENERATION_ATTRIBUTES if not _present(attributes.get(field))
        ]
        if missing:
            incomplete_generations.append(
                {
                    "observation": str(observation.get("name") or "<unnamed>"),
                    "missing": missing,
                }
            )

    failure_summaries = [
        observation
        for observation in observations
        if observation.get("name") == "kolibri.crewai.failure_summary"
    ]
    incomplete_failure_summaries: list[dict[str, Any]] = []
    failure_summary_tools: list[str] = []
    failure_types: list[str] = []
    for observation in failure_summaries:
        attributes = observation_attributes(observation)
        missing = [
            field
            for field in REQUIRED_FAILURE_SUMMARY_ATTRIBUTES
            if not _present(attributes.get(field))
        ]
        if str(observation.get("level") or "").upper() != "ERROR":
            missing.append("OTel ERROR status (Langfuse level=ERROR)")
        if missing:
            incomplete_failure_summaries.append(
                {
                    "observation": str(observation.get("name")),
                    "missing": missing,
                }
            )
        if _present(attributes.get("kolibri.failure.tool.name")):
            failure_summary_tools.append(str(attributes["kolibri.failure.tool.name"]))
        if _present(attributes.get("error.type")):
            failure_types.append(str(attributes["error.type"]))

    application_failures: list[dict[str, Any]] = []
    for observation in observations:
        attributes = observation_attributes(observation)
        operation = attributes.get("gen_ai.operation.name")
        is_error = str(observation.get("level") or "").upper() == "ERROR"
        if operation not in RUN_OPERATIONS | {"execute_tool"} or not is_error:
            continue
        if not _present(attributes.get("error.type")):
            application_failures.append(
                {
                    "observation": str(observation.get("name") or "<unnamed>"),
                    "reason": "ERROR application operation is missing error.type",
                }
            )

    composite_observations = [
        observation
        for observation in observations
        if _present(
            observation_attributes(observation).get(
                "kolibri.composite.parent.tool.name"
            )
        )
    ]
    composite_children: list[str] = []
    incomplete_composites: list[dict[str, Any]] = []
    for observation in composite_observations:
        attributes = observation_attributes(observation)
        missing = [
            field for field in REQUIRED_COMPOSITE_ATTRIBUTES if not _present(attributes.get(field))
        ]
        child = attributes.get("kolibri.composite.child.operation.name")
        if _present(child):
            composite_children.append(str(child))
        if missing:
            incomplete_composites.append(
                {
                    "observation": str(observation.get("name") or "<unnamed>"),
                    "missing": missing,
                }
            )
    composite_children = _unique(composite_children)
    expected_child_set = set(expected_composite_children)

    missing_context = [
        field for field in REQUIRED_CONTEXT_ATTRIBUTES if not _present(root_attributes.get(field))
    ]
    invalid_context = []
    if _present(root_attributes.get("kolibri.runtime.name")) and root_attributes.get(
        "kolibri.runtime.name"
    ) != "crewai":
        invalid_context.append("kolibri.runtime.name")
    if _present(root_attributes.get("kolibri.channel")) and root_attributes.get(
        "kolibri.channel"
    ) not in {"chat", "voice", "messaging"}:
        invalid_context.append("kolibri.channel")
    context_valid = (
        not missing_context
        and root_attributes.get("kolibri.runtime.name") == "crewai"
        and root_attributes.get("kolibri.channel") in {"chat", "voice", "messaging"}
    )

    trace_identity_passed = (
        trace.get("id") == requested_trace_id and _present(trace.get("name"))
    )
    failure_summary_passed = (
        (not require_failure_summary or bool(failure_summaries))
        and not incomplete_failure_summaries
    )
    composite_passed = (
        expected_child_set.issubset(set(composite_children))
        and not incomplete_composites
    )

    checks = [
        _check(
            "trace_identity",
            "Trace and root identity",
            trace_identity_passed,
            f"trace={trace.get('id') or '<missing>'}; name={trace.get('name') or '<missing>'}",
        ),
        _check(
            "canonical_run",
            "Exactly one canonical run observation",
            len(run_observations) == 1,
            f"found={len(run_observations)}",
        ),
        _check(
            "run_operation",
            "Canonical run operation",
            root_operation in RUN_OPERATIONS,
            f"operation={root_operation or '<missing>'}",
        ),
        _check(
            "application_context",
            "Required application context",
            context_valid,
            "complete"
            if context_valid
            else "missing/invalid=" + ",".join(missing_context + invalid_context),
        ),
        _check(
            "agents",
            "Canonical agent observations",
            bool(agents) and not incomplete_agents,
            f"detected={len(agents)}; incomplete={len(incomplete_agents)}",
        ),
        _check(
            "tools_detected",
            "Tool detection (Final Schema first, explicit legacy fallback)",
            tool_detection_passed,
            "detected=" + (",".join(tools["detected"]) or "<none>"),
        ),
        _check(
            "tool_schema",
            "Final Trace Schema tool fields",
            tool_schema_passed,
            (
                f"canonical={len(tools['final_schema'])}; "
                f"legacy={len(tools['legacy_fallback'])}; incomplete={len(tools['incomplete'])}"
            ),
        ),
        _check(
            "generations_detected",
            "Canonical model generations",
            bool(generations),
            f"detected={len(generations)}",
        ),
        _check(
            "generation_schema",
            "Required generation fields",
            bool(generations) and not incomplete_generations,
            f"incomplete={len(incomplete_generations)}",
        ),
        _check(
            "failure_contract",
            "Failure observations and safe summary contract",
            not application_failures and failure_summary_passed,
            (
                f"summaries={len(failure_summaries)}; "
                f"incomplete={len(incomplete_failure_summaries)}; "
                f"application_failures={len(application_failures)}"
            ),
        ),
        _check(
            "composite_contract",
            "Composite child-operation contract",
            composite_passed,
            f"children={len(composite_children)}; incomplete={len(incomplete_composites)}",
        ),
    ]
    passed_count = sum(1 for check in checks if check["passed"])
    failed_checks = [check for check in checks if not check["passed"]]

    canonical_tool_observations = [
        observation
        for observation in observations
        if observation_attributes(observation).get("gen_ai.operation.name")
        == "execute_tool"
    ]
    span_kind = {
        "canonical_generations": _span_kind_result(generations, "CLIENT"),
        "canonical_tools": _span_kind_result(canonical_tool_observations, "INTERNAL"),
        "api_boundary": (
            "The checker validates SpanKind only when the API exposes it; "
            "absence is reported as not_exposed, never as a pass."
        ),
    }

    warnings: list[str] = []
    if tools["legacy_fallback"]:
        warnings.append(
            "Legacy tool representations were detected for compatibility; they do not satisfy the Final Trace Schema tool-field check."
        )
    if any(result["status"] == "not_exposed" for result in span_kind.values() if isinstance(result, dict)):
        warnings.append("Langfuse API data did not expose SpanKind for one or more relevant observation types.")

    return {
        "trace": {
            "id": trace.get("id"),
            "name": trace.get("name"),
            "canonical_run_observation": root.get("name") if root else None,
            "observation_count": len(observations),
        },
        "agents": agents,
        "tools": tools,
        "canonical_generation_count": len(generations),
        "failure_summaries": {
            "count": len(failure_summaries),
            "tools": _unique(failure_summary_tools),
            "error_types": _unique(failure_types),
            "incomplete": incomplete_failure_summaries,
        },
        "composite_children": composite_children,
        "required_application_context": {
            field: root_attributes.get(field) for field in REQUIRED_CONTEXT_ATTRIBUTES
        },
        "validation": {
            "passed": passed_count == len(checks),
            "passed_count": passed_count,
            "total_count": len(checks),
            "coverage_percent": round((passed_count / len(checks)) * 100, 1),
            "checks": checks,
            "failures": failed_checks,
            "details": {
                "incomplete_agents": incomplete_agents,
                "incomplete_generations": incomplete_generations,
                "application_failures": application_failures,
                "incomplete_composites": incomplete_composites,
            },
        },
        "span_kind": span_kind,
        "boundaries": {
            "structural": "Validated from trace and observation fields exposed by the Langfuse public API.",
            "privacy": "Not validated by this checker; requires controlled trace-content inspection and an allow-list review.",
            "cost": "Not validated by this checker; requires comparison with approved LiteLLM Proxy evidence.",
            "hierarchy": "Partially inspectable through parent observation IDs; intended semantic hierarchy still requires trace inspection.",
        },
        "warnings": warnings,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-id", required=True)
    parser.add_argument("--expected-tool", action="append", default=[])
    parser.add_argument("--require-failure-summary", action="store_true")
    parser.add_argument("--expected-composite-child", action="append", default=[])
    parser.add_argument("--no-legacy-tool-fallback", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    payload = json.load(sys.stdin)
    report = validate_trace(
        _mapping(payload.get("trace")),
        list(payload.get("observations") or []),
        requested_trace_id=args.trace_id,
        expected_tools=args.expected_tool,
        require_failure_summary=args.require_failure_summary,
        expected_composite_children=args.expected_composite_child,
        allow_legacy_tool_fallback=not args.no_legacy_tool_fallback,
    )
    json.dump(report, sys.stdout, separators=(",", ":"))


if __name__ == "__main__":
    main()
