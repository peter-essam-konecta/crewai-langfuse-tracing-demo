# AI Agent Instructions

This repository is the canonical Task 005 R&D and developer-handoff reference for CrewAI tracing through Konecta's LiteLLM Proxy into Langfuse. It is a tested reference, not a production deployment.

Do not infer missing facts. Label anything not established by code, tests, or recorded evidence as unknown or pending validation.

## Required reading

Read these three documents before proposing an integration:

1. `docs/trace-schema-contract.md` — exact field ownership and privacy rules.
2. `docs/developer-guide.md` — dependencies, integration sequence, and acceptance checks.
3. `docs/trace-verification-and-evidence.md` — claims supported by recorded live evidence.

Read these only when relevant:

- `docs/architecture-decisions-and-faq.md` for the instrumentor decision and known limitations.
- `docs/implementation-handoff.md` for ownership and approval boundaries.
- `docs/troubleshooting.md` for setup or trace failures.

Use this precedence when sources disagree:

1. The approved Final Trace Schema rules summarized in the schema contract govern fields and privacy.
2. Source code and passing tests govern current interfaces and behavior.
3. The evidence document governs validated live claims.
4. Explanatory documentation never overrides those sources.

Stop and report an unresolved contradiction before implementing it.

## Architectural invariants

- Start with OpenLIT automatic CrewAI tracing. Do not add manual spans around normal workflows, agents, tasks, or tools.
- CrewAI/OpenLIT owns workflow telemetry. LiteLLM Proxy owns canonical model generations, tokens, latency, and cost.
- Count canonical generations, not HTTP transport observations, for model usage and cost.
- `configure_tracing()` explicitly instruments HTTPX and aiohttp for W3C context propagation. Verify the connected result in the target environment.
- Use `FailureAdapter` only for a safe tool-failure/retry summary.
- Use `CompositeToolAdapter` only for selected internal operations hidden inside a parent tool.
- Delegation uses automatic tracing and no custom adapter.
- Never invent `gen_ai.*` fields. Use approved `kolibri.*` extensions.
- Never capture prompts, completions, tool payloads, customer identifiers, raw exception messages, or stack traces.
- Do not enable OpenInference, OpenLLMetry, or CrewAI hosted tracing beside OpenLIT.

## Maintained interfaces

- Tracing lifecycle: `configure_tracing(settings)` and `flush_tracing()` in `src/crewai_langfuse_demo/tracing.py`.
- Failure integration: `FailureAdapter.install()`, `complete(crew_completed=...)`, and `uninstall()`; see `examples/failure_adapter_example.py`.
- Composite integration: `CompositeToolAdapter.run_child(...)`; see `examples/composite_tool_adapter_example.py`.
- End-to-end runner: `src/crewai_langfuse_demo/main.py`.

The repository does not provide `init_tracing`, `observe_crew_failures`, or `observe_child_operation`.

## Validation

Run from the repository root:

```powershell
.\scripts\setup.ps1
.\scripts\run-tests.ps1

.\scripts\run-basic.ps1
.\scripts\run-retry.ps1
.\scripts\run-delegation.ps1
.\scripts\run-composite-tool.ps1

.\scripts\check-trace.ps1 -TraceId <TRACE_ID>
```

The first two commands are local. Scenario and trace commands require approved `.env` values and external services. `check-trace.ps1` is a structural summary, not a privacy or cost audit.

Historical local-Groq and V3-era cost-reproduction files are intentionally absent from `main`. They are preserved in Git tag `archive-v3-local-proxy-2026-08-25` and must not be restored into the current integration path without an explicit decision.
