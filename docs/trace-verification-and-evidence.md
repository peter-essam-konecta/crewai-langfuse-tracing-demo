# Trace Verification and Recorded Evidence

> **Status:** Evidence-backed Task 005 reference. Links may require access to the Langfuse Cloud project. Do not assign a trace to a scenario unless the scenario is recorded here or revalidated.

## Previously recorded final-schema-alignment traces

These three trace IDs are the recorded live evidence for the repository after alignment to the approved Final Trace Schema:

| Scenario | Command | Evidence | What was validated |
| :--- | :--- | :--- | :--- |
| Basic workflow | `.\scripts\run-basic.ps1` | [Trace `858addf0172cd90a22b539390c877117`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/858addf0172cd90a22b539390c877117) | Automatic CrewAI workflow with three agents, three tasks, three tools, and connected model activity. |
| Retry/failure | `.\scripts\run-retry.ps1` | [Trace `58c18eccd3edf5cc78cdf192185f2ffb`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/58c18eccd3edf5cc78cdf192185f2ffb) | Controlled retry plus one safe `kolibri.crewai.failure_summary`. |
| Composite tool | `.\scripts\run-composite-tool.ps1` | [Trace `b210082a4bead567b5e993c4f4e23c26`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/b210082a4bead567b5e993c4f4e23c26) | Parent tool plus two selected child-operation observations from the composite adapter. |

The delegation scenario is implemented and was validated during Task 005, but this repository does not currently record a dedicated canonical final-schema delegation trace ID. Run `.\scripts\run-delegation.ps1` and capture fresh evidence before citing a specific trace.

Trace `0edbf7991a3fc7b45817d81b95eff248` is historical composite-tool evidence from 24 July 2026. It must not be presented as delegation evidence or as the later final-schema validation trace.

These traces remain valid evidence for the scenario outcomes stated in the table. They are not a current eleven-of-eleven claim. The corrected checker now distinguishes compatible legacy exporter representations from actual Final Trace Schema compliance.

## Validation-gap closure audit: 2026-08-25

### Historical 90.9% root cause

Historical controlled-failure trace [`19b3826afad90704e06931d600655431`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/19b3826afad90704e06931d600655431) was evaluated by `poc/scripts/inspect-coverage.ps1`. That script's tool check read only observations named `Tool Usage` and the legacy `tool_name` field, plus the safe failure-summary tool name. The trace stored the two successful normal tools through `gen_ai.operation.name = "execute_tool"` and `gen_ai.tool.name`, so the legacy check missed them and returned **10 of 11 (90.9%)**.

The repository checker now detects Final Trace Schema tool fields first and recognizes `Tool Usage` + `tool_name` only as an explicit compatibility fallback. Tool detection and Final-Schema compliance are separate checks: a legacy tool can be found without being incorrectly declared schema-compliant, and an observation missing its required tool name still fails.

The historical 90.9% record is retained. It is superseded as a diagnosis of tool coverage, but trace `19b382...` is not relabeled as a fresh Final-Schema 11/11 result. When reassessed with the new, stricter eleven-check Final-Schema validator, it passes 7 of 11; that result uses a different current contract and must not be compared numerically as if it were the same historical checklist.

### Fresh live scenarios

All four maintained workflows completed successfully against the configured Langfuse + Konecta LiteLLM environment:

| Scenario | Fresh trace | Functional result |
| :--- | :--- | :--- |
| Basic | [`f8614db7274b258ec2d297652f545704`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/f8614db7274b258ec2d297652f545704) | Completed with the expected safe delayed-order response. |
| Retry/failure | [`58303b331e2c5cd0607d6539fde7bc90`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/58303b331e2c5cd0607d6539fde7bc90) | Failed twice, succeeded on attempt three, and emitted one complete safe failure summary. |
| Delegation | [`3d2afa78efc0265431da77c33b4cde26`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/3d2afa78efc0265431da77c33b4cde26) | Completed with automatic tracing only. |
| Composite tool | [`6d349d4f39c22f6dc9f6cda9af4e0acb`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/6d349d4f39c22f6dc9f6cda9af4e0acb) | Completed with both expected composite child operations. |

The corrected Retry validation legitimately returned **7 of 11 (63.6%)**, not 11 of 11. Passed checks were trace/root identity, one canonical run, the run operation, required application context, compatibility-aware tool detection, the complete safe failure-summary contract, and the not-required composite contract. The four failures were:

- OpenLIT exported 19 internal graph observations as `invoke_agent` without required `gen_ai.agent.name`;
- the successful normal tool came from CrewAI telemetry as `Tool Usage` + `tool_name`, so compatibility detection passed but the Final Trace Schema tool-field check failed;
- no LiteLLM Proxy-owned canonical generation joined the fresh workflow trace; and
- generation-field validation consequently had no canonical generation to inspect.

Fresh Composite validation also returned **7 of 11**. Its two repository-owned child operations passed the Final-Schema composite contract; the automatic parent tool remained a legacy fallback, and the same agent/generation gaps remained.

Therefore, **no fresh live 11/11 claim was produced**. The local regression fixture proves the corrected logic can produce a legitimate 11/11 only when all eleven required structures are present; it is test evidence, not live environment evidence.

### SpanKind evidence

Automated SDK-level tests prove:

- `CompositeToolAdapter` emits its repository-owned `execute_tool` child span as `SpanKind.INTERNAL`;
- OpenLIT `1.44.0`'s actual CrewAI tool wrapper emits `execute_tool` as `SpanKind.INTERNAL`; and
- the checker accepts `CLIENT` for a canonical generation and `INTERNAL` for a canonical tool only when those values are present in inspected API data.

The Langfuse public trace and observation API responses inspected on 25 August exposed no SpanKind field. The fresh Retry trace also contained no connected Proxy-owned canonical generation. Consequently:

- normal automatic tool SpanKind is **not proven end to end** by fresh Langfuse evidence;
- canonical LiteLLM generation `SpanKind.CLIENT` is **not proven** in this environment; and
- exporter- or collector-level confirmation remains a target-development validation item.

No code changed or reinterpreted the approved Final Trace Schema, and no automatic or remote SpanKind was overwritten to manufacture a passing result.

## Code-derived scenario map

This section describes the maintained source code. It is not a verbatim claim about exporter-generated span names.

### Basic workflow

- Crew: `Customer Support - Delayed Order`
- Agents: `Order status specialist`, `Refund policy specialist`, `Customer response specialist`
- Tools: `lookup_order_status`, `get_refund_policy`, `create_response_checklist`
- Adapter: none

### Retry/failure

- Crew: `Customer Support - Retry & Recovery`
- Agent: `Retry-aware order specialist`
- Tool: `lookup_retryable_order_status`
- Adapter output: `kolibri.crewai.failure_summary` with `kolibri.failure.*` fields

The deterministic demo fails twice and succeeds on the third tool call. Depending on CrewAI event behavior, the final outcome is recorded as `retry_succeeded`; do not document a different outcome without inspecting the trace.

### Composite tool

- Crew: `Customer Support - Composite Operations`
- Agent: `Order exception specialist`
- Parent tool: `resolve_order_exception`
- Child operations: `lookup_order_status_for_exception`, `lookup_policy_for_exception`
- Adapter: `CompositeToolAdapter`

### Delegation

- Crew: `Customer Support - Agent Delegation`
- Coordinator: `Customer support exception coordinator`
- Specialist: `Policy exception specialist`
- Specialist tool: `lookup_exception_policy`
- Adapter: none
- Known limitation: automatic tracing did not provide a separately named delegated policy task in the Task 005 coverage review.

## Local verification boundaries

Run:

```powershell
.\scripts\check-trace.ps1 -TraceId <TRACE_ID>
```

The script reports trace/root identity, required application context, canonical agents, Final-Schema and compatibility-fallback tools, canonical generations, safe failure summaries, composite children, eleven structural checks, and any available SpanKind. It exits with code `1` when a structural requirement fails. It does not inspect message content, prove every parent-child relationship, compare costs with Proxy evidence, or treat missing SpanKind as a pass. Perform those checks separately before approving a target integration.
