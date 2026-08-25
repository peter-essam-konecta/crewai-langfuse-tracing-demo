# CrewAI Implementation Mapping to the Final Trace Schema

> **Status:** Repository-owned CrewAI subset of the approved Issue #63 Final Trace Schema. This file maps the current code to that contract; it is not a replacement for the full organization-wide cross-channel specification.

## Governing rules

1. Use official OpenTelemetry GenAI semantic attributes for standardized concepts.
2. Never invent keys under `gen_ai.*`; use approved `kolibri.*` extensions for Kolibri-specific concepts.
3. The real model vendor belongs in `gen_ai.provider.name`; LiteLLM is the Proxy, and CrewAI is recorded as `kolibri.runtime.name`.
4. Count only canonical model generations for tokens and cost. HTTP transport observations are supporting telemetry, not additional model calls.
5. Do not record raw messages, tool payloads, customer identifiers, exception messages, or stack traces.

## Application-owned context attributes

`configure_tracing()` supplies these attributes through OpenLIT's `custom_span_attributes`:

| Attribute | Source | Example |
| :--- | :--- | :--- |
| `kolibri.tenant.id` | `Settings.tenant_id` | `demo-workspace` |
| `gen_ai.conversation.id` | `Settings.conversation_id` | `demo-session-001` |
| `gen_ai.agent.id` | `Settings.agent_id` | `crew_customer_support_01` |
| `kolibri.runtime.name` | Fixed by this implementation | `crewai` |
| `kolibri.channel` | `Settings.channel` | `chat` |

`langfuse.trace.name` and `gen_ai.workflow.name` are added only when `LANGFUSE_TRACE_NAME` or `CREWAI_TRACE_NAME` is set and the automatic span is a workflow span.

## Automatically owned observations

OpenLIT is expected to create CrewAI workflow, agent, task, and normal tool observations. Exporter-provided names and optional fields can vary by library version, so validate them in a fresh target-environment trace instead of hardcoding an assumed tree.

The approved contract requires tool operations to use:

- `gen_ai.operation.name = "execute_tool"`
- `gen_ai.tool.name = <tool name>`

`scripts/check-trace.ps1` detects those fields first. It can recognize the current CrewAI legacy `Tool Usage` + `tool_name` representation as an explicit compatibility fallback, but that fallback does not pass the separate Final Trace Schema tool-field check. This distinction prevents a legacy exporter-name mismatch from hiding a real contract gap.

LiteLLM Proxy owns canonical generation fields, including the real provider and model identifiers, input/output token usage, finish reasons, and cost. The repository normalizes `litellm.cost.total` to `gen_ai.usage.cost` when the former is present on a span. The exact Proxy-emitted field set must be verified against the deployed Proxy version.

## Failure adapter extension

`FailureAdapter` emits one span named `kolibri.crewai.failure_summary` for each recorded failed tool. Its exact attributes are:

| Attribute | Meaning | Allowed examples |
| :--- | :--- | :--- |
| `kolibri.failure.tool.name` | Failed tool identifier | `lookup_retryable_order_status` |
| `error.type` | Standard low-cardinality error category | `timeout`, `tool_execution_failed` |
| `kolibri.failure.error.type` | Kolibri copy of the safe error category | `controlled_test_failure` |
| `kolibri.failure.retry.count` | Retry attempts inferred from CrewAI events | `2` |
| `kolibri.failure.final.outcome` | Safe final state | `retry_succeeded`, `fallback_completed`, `aborted` |

The span receives OTel `ERROR` status with the constant description `safe tool failure`. It never copies the raw exception text.

## Composite-tool extension

`CompositeToolAdapter.run_child()` emits one child span for each selected hidden operation:

| Attribute | Value |
| :--- | :--- |
| Span name | `execute_tool <child operation>` |
| `gen_ai.operation.name` | `execute_tool` |
| `gen_ai.tool.name` | Child operation name |
| `kolibri.composite.parent.tool.name` | Parent tool name |
| `kolibri.composite.child.operation.name` | Child operation name |
| `kolibri.composite.child.final.outcome` | `succeeded` or `failed` |

There is no `kolibri.system` field in the current adapter because the implementation does not receive a system identifier.

## OpenTelemetry SpanKind

The approved contract requires:

The current [OpenTelemetry Trace API](https://opentelemetry.io/docs/specs/otel/trace/api/#spankind) and [GenAI span conventions](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md) are secondary technical references. The approved Final Trace Schema remains authoritative for this project.

| Operation | Required SpanKind | Current evidence |
| :--- | :--- | :--- |
| Canonical model generation | `CLIENT` | Not yet proven end to end. The Langfuse public API used by this repository does not expose SpanKind, and the fresh 25 August Retry trace did not contain a connected Proxy generation. |
| Tool execution | `INTERNAL` | Proven locally for the repository-owned `CompositeToolAdapter` span and for OpenLIT `1.44.0`'s CrewAI tool wrapper through SDK-exported spans. The fresh Langfuse API response does not expose the actual normal-tool SpanKind. |

`CompositeToolAdapter` sets `SpanKind.INTERNAL` when it creates its selected child-operation span. The repository does not alter SpanKind on automatic OpenLIT spans or remote LiteLLM Proxy generations.

## Privacy controls and validation boundary

The implementation sets `capture_message_content=False` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=no_content`. These are required controls, not proof of complete redaction across every dependency or exporter version. Production approval requires inspection of a fresh trace and an allow-list/redaction review in the target environment. The checker validates only fields exposed by the Langfuse public API; it does not claim privacy, Proxy cost parity, complete hierarchy, or unavailable SpanKind evidence.
