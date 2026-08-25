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

For tool operations, the repository uses the standard values:

- `gen_ai.operation.name = "execute_tool"`
- `gen_ai.tool.name = <tool name>`

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

## Privacy controls and validation boundary

The implementation sets `capture_message_content=False` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=no_content`. These are required controls, not proof of complete redaction across every dependency or exporter version. Production approval requires inspection of a fresh trace and an allow-list/redaction review in the target environment.
