# AI Agent Instructions and Repository Source of Truth

This repository is the canonical Task 005 R&D and developer-handoff reference for CrewAI tracing with OpenLIT, LiteLLM Proxy, OpenTelemetry, and Langfuse. It is a tested teaching implementation, not a production deployment or a substitute for development-environment validation.

Do not fill missing facts with assumptions. If the code, tests, or verified evidence do not establish a claim, label it as unknown or pending validation.

## 1. Required reading order

Read these files before proposing or changing an integration:

1. `AGENTS.md`
2. `docs/trace-schema-contract.md`
3. `docs/developer-guide.md`
4. `docs/architecture-decisions-and-faq.md`
5. `docs/implementation-handoff.md`
6. `docs/trace-verification-and-evidence.md`
7. `README.md`

Use this precedence when sources disagree:

1. The approved Final Trace Schema rules summarized in `docs/trace-schema-contract.md` govern field names and privacy.
2. Source code and passing tests govern the interfaces and current behavior in this repository.
3. `docs/trace-verification-and-evidence.md` governs which live outcomes have recorded evidence.
4. Guides and FAQs explain those sources; they do not override them.

Stop and report any unresolved contradiction before implementing it.

## 2. Architectural invariants

### Automatic first

- Do not create manual spans around normal CrewAI workflows, agents, tasks, or tools. OpenLIT supplies that framework telemetry.
- Use `FailureAdapter` only when a run needs a safe summary of tool failure, retry count, and final outcome.
- Use `CompositeToolAdapter` only for selected internal operations that automatic tracing cannot see inside a parent tool.
- Standard delegation uses automatic tracing and no custom adapter.

### One owner for each telemetry layer

- CrewAI/OpenLIT owns workflow, agent, task, and tool telemetry.
- LiteLLM Proxy owns canonical model generations, tokens, latency, and cost.
- HTTP transport observations and model generations describe the same request; dashboards must count only canonical generations.
- The application explicitly instruments HTTPX and aiohttp so the active W3C trace context reaches the Proxy. Verify the resulting hierarchy in the target environment; do not assume it.

### Schema and privacy

- Never invent attributes in the reserved `gen_ai.*` namespace. Use approved `kolibri.*` extensions for repository-specific fields.
- Preserve `kolibri.tenant.id`, `gen_ai.conversation.id`, `gen_ai.agent.id`, `kolibri.runtime.name`, and `kolibri.channel` on automatic spans.
- Never capture prompts, completions, tool arguments, tool outputs, customer identifiers, raw exception messages, or stack traces.
- `capture_message_content=False` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=no_content` reduce content capture. They do not prove that every exporter is safe; inspect a fresh trace before approval.

### One automatic instrumentation library

- OpenLIT is the selected and tested automatic instrumentation library for this POC.
- Do not enable OpenInference, OpenLLMetry, or CrewAI hosted tracing in the same process because the tested alternatives created duplicate or fragmented telemetry.

## 3. Current implementation map

```text
src/crewai_langfuse_demo/
|-- config.py                  # Loads non-secret defaults and required secrets.
|-- llm.py                     # Routes CrewAI model calls through LiteLLM Proxy.
|-- main.py                    # Configures tracing before importing CrewAI workflows.
|-- tracing.py                 # OpenLIT, OTLP export, privacy, and HTTP context propagation.
|-- adapters/
|   |-- failure.py             # FailureAdapter: error-only safe summary.
|   `-- composite_tool.py      # CompositeToolAdapter: selected child operations.
|-- basic/                     # Automatic-only three-agent example.
`-- advanced/                  # Retry, delegation, and composite examples.
```

The smallest maintained adapter integrations are in `examples/`. Prefer linking to those files instead of duplicating their code in new documentation.

## 4. Exact supported interfaces

Configure tracing before importing modules that import CrewAI:

```python
from crewai_langfuse_demo.config import load_settings
from crewai_langfuse_demo.tracing import configure_tracing, flush_tracing

settings = load_settings()
configure_tracing(settings)

from crewai_langfuse_demo.basic.crew import build_crew

try:
    result = build_crew(settings).kickoff()
finally:
    flush_tracing()
```

For a retry/failure run, use `FailureAdapter.install()`, `FailureAdapter.complete(crew_completed=...)`, and `FailureAdapter.uninstall()` exactly as shown in `examples/failure_adapter_example.py`.

For selected operations inside a composite tool, use `CompositeToolAdapter.run_child(parent_tool=..., child_operation=..., operation=...)` exactly as shown in `examples/composite_tool_adapter_example.py`.

The repository does not provide `init_tracing`, `observe_crew_failures`, or `observe_child_operation` APIs.

## 5. Validation commands

Run from the repository root:

```powershell
# Local unit and repository-contract tests; no external calls.
.\scripts\run-tests.ps1

# Live scenarios; require approved .env values and services.
.\scripts\run-basic.ps1
.\scripts\run-retry.ps1
.\scripts\run-delegation.ps1
.\scripts\run-composite-tool.ps1

# Read-only trace summary. This does not perform a privacy or cost audit.
.\scripts\check-trace.ps1 -TraceId <TRACE_ID>
```

The test suite uses Python's standard `unittest` runner through `scripts/run-tests.ps1`; `pytest` is not a repository dependency.

## 6. Prohibited patterns

| Do not | Reason | Use instead |
| :--- | :--- | :--- |
| Add manual normal-operation spans | Duplicates automatic CrewAI observations | OpenLIT automatic tracing |
| Enable multiple CrewAI instrumentors | Creates duplicate or fragmented traces | OpenLIT only in this pattern |
| Count HTTP transport spans as model calls | Double-counts usage and cost | Canonical LiteLLM generation spans |
| Store credentials or customer content | Security and privacy risk | Environment/secret management and low-cardinality metadata |
| Copy an unverified API or schema key from prose | Documentation can drift | Check source, tests, and the schema mapping |
| Claim production readiness from POC evidence | Target services and enterprise environments differ | Run the acceptance checklist in development/staging |

Non-secret reference endpoints may appear as configurable defaults. Keys and credentials must never be committed.
