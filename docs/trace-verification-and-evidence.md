# Trace Verification and Recorded Evidence

> **Status:** Evidence-backed Task 005 reference. Links may require access to the Langfuse Cloud project. Do not assign a trace to a scenario unless the scenario is recorded here or revalidated.

## Canonical final-schema validation traces

These three trace IDs are the recorded live evidence for the repository after alignment to the approved Final Trace Schema:

| Scenario | Command | Evidence | What was validated |
| :--- | :--- | :--- | :--- |
| Basic workflow | `.\scripts\run-basic.ps1` | [Trace `858addf0172cd90a22b539390c877117`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/858addf0172cd90a22b539390c877117) | Automatic CrewAI workflow with three agents, three tasks, three tools, and connected model activity. |
| Retry/failure | `.\scripts\run-retry.ps1` | [Trace `58c18eccd3edf5cc78cdf192185f2ffb`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/58c18eccd3edf5cc78cdf192185f2ffb) | Controlled retry plus one safe `kolibri.crewai.failure_summary`. |
| Composite tool | `.\scripts\run-composite-tool.ps1` | [Trace `b210082a4bead567b5e993c4f4e23c26`](https://cloud.langfuse.com/project/cmrupomt005u1ad0d12pcr750/traces/b210082a4bead567b5e993c4f4e23c26) | Parent tool plus two selected child-operation observations from the composite adapter. |

The delegation scenario is implemented and was validated during Task 005, but this repository does not currently record a dedicated canonical final-schema delegation trace ID. Run `.\scripts\run-delegation.ps1` and capture fresh evidence before citing a specific trace.

Trace `0edbf7991a3fc7b45817d81b95eff248` is historical composite-tool evidence from 24 July 2026. It must not be presented as delegation evidence or as the later final-schema validation trace.

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

The script reports the trace name, observation count, detected agents, tools, generation count, failure summaries, and composite children. It does not inspect message content, validate every parent-child relationship, or compare costs with a Proxy ledger. Perform those checks separately before approving a target integration.
