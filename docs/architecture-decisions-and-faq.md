# Architecture Decisions and Technical FAQ

> **Status:** Evidence-backed Task 005 R&D decisions for GitHub issue #65. Claims are scoped to the tested versions and POC environment.

## ADR 1: Select OpenLIT as the automatic baseline

The POC compared three instrumentors on the same safe CrewAI workflow:

| Tested library | CrewAI workflow visible | Connected to Proxy telemetry in one trace | Observed content behavior | Decision |
| :--- | :---: | :---: | :--- | :--- |
| OpenLIT `1.44.0` | Yes | Yes | Message-content capture could be disabled | Selected baseline |
| OpenInference CrewAI `1.1.10` | Yes | No in the test | Truncated prompt content appeared by default | Rejected for this pattern |
| OpenLLMetry CrewAI `0.62.1` | Yes | No in the test | Prompt/completion content appeared by default | Rejected for this pattern |

OpenLIT was the only tested configuration that produced the required connected trace. This is an empirical POC result, not a universal claim about every version or configuration of those libraries.

## ADR 2: Keep model generation and cost ownership at LiteLLM Proxy

The Proxy sees the provider response and is therefore the appropriate source for generation tokens, latency, and calculated cost. CrewAI/OpenLIT remains responsible for workflow telemetry. This separation avoids two competing generation records.

An isolated local ledger comparison matched Langfuse cost within floating-point rounding. The POC did not prove parity with enterprise invoices or every enterprise spend database; that remains a target-environment validation item.

## ADR 3: Use explicit adapters only for measured gaps

- Normal workflow, agent, task, parent-tool, and delegation telemetry remains automatic.
- `FailureAdapter` summarizes safe failure metadata because the tested automatic export did not preserve the failed-tool identity, retry count, and final outcome clearly.
- `CompositeToolAdapter` exposes selected internal operations because automatic tracing sees only the parent CrewAI tool.

## FAQ

### Why is no delegation adapter used?

The tested automatic trace made coordinator/specialist execution visible enough for the POC. Coverage was 87.5% because there was no separately named delegated policy task. Adding a wrapper would duplicate automatic observations without resolving that upstream naming limitation.

### How does context reach LiteLLM Proxy?

`configure_tracing()` explicitly instruments both HTTPX and aiohttp. Those OpenTelemetry client instrumentors inject the active W3C `traceparent` header into outgoing requests. The Proxy must be configured to extract that context. Verify that the generation joins the intended workflow hierarchy in development; the code alone cannot prove the remote Proxy configuration.

### Does OpenLIT add no dependencies?

No. In this repository, `openlit==1.44.0` is a direct dependency and it brings transitive OpenTelemetry packages. A target service must inspect its own dependency graph. If OpenLIT is not already present, adopting this exact pattern adds it.

### Are the adapters production-ready?

They are reusable, privacy-conscious, unit-tested R&D references. Production use requires a code review, dependency compatibility check, target-environment traces, privacy validation, and technical approval.

### Did the corrected checker produce a fresh 11/11?

No. The 25 August Retry workflow completed, but its schema-strict result was 7/11. Compatibility-aware detection found the legacy normal tool, while the separate Final-Schema check correctly failed it. The same trace also exposed incomplete automatic agent operations and no connected Proxy-owned canonical generation. This is a current dependency/environment gap, not a reason to weaken the checker or change the approved schema.

### What remains open?

- Development/staging implementation in the target CrewAI service
- Target dependency behavior that emits Final-Schema normal-tool and agent-step fields without relying on compatibility fallbacks
- Enterprise secret and Proxy configuration
- Fresh connected-generation, healthy, failure, cost, hierarchy, privacy, and exporter-level SpanKind evidence
- Production approval and GitHub issue closure by the responsible owners
