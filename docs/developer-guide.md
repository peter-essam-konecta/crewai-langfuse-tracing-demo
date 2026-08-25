# CrewAI Tracing Developer Integration Guide

> **Status:** R&D-validated reference pattern. Development/staging validation and production approval remain the development team's responsibility.

## Purpose

This guide explains how to adapt the repository's automatic-first CrewAI tracing pattern. The target outcome is one connected Langfuse trace containing automatic CrewAI workflow telemetry and LiteLLM Proxy-owned model generations, without raw message content.

The POC demonstrates that outcome. It does not guarantee it in a different service, dependency set, Proxy, or exporter; validate every acceptance item after integration.

## Data flow

```text
CrewAI application
  -> OpenLIT automatic workflow/agent/task/tool telemetry
  -> OTLP export to Langfuse

CrewAI model request
  -> instrumented HTTPX/aiohttp request with W3C trace context
  -> LiteLLM Proxy
  -> canonical model generation, tokens, latency, and cost in Langfuse
```

## Six-step integration recipe

### 1. Review dependencies before adding them

The validated repository pins are:

```text
crewai==1.15.2
openlit==1.44.0
litellm==1.91.2
opentelemetry-instrumentation-aiohttp-client==0.63b1
opentelemetry-instrumentation-httpx==0.63b1
python-dotenv==1.2.2
```

These are the direct dependencies in `requirements.txt`; OpenLIT and CrewAI bring additional transitive OpenTelemetry packages. Do not copy loose version ranges into a target service. First compare its existing dependency graph, then add or align only the packages the reviewed implementation needs.

Important: OpenLIT is already a dependency of this reference repository. Adding this pattern to another repository introduces a new direct dependency there unless that repository already includes OpenLIT.

### 2. Configure environment values securely

The current `Settings` implementation reads:

```text
LANGFUSE_BASE_URL
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
LITELLM_PROXY_HOST
LITELLM_MASTER_KEY
LITELLM_MODEL
OTEL_SERVICE_NAME
DEMO_TENANT_ID
DEMO_CONVERSATION_ID
DEMO_AGENT_ID
DEMO_CHANNEL
```

Use the target service's secret manager for keys. The `DEMO_*` names are teaching-repository names; map them deliberately to approved service configuration rather than silently inventing replacements.

### 3. Configure tracing before importing CrewAI workflows

Use the maintained implementation instead of recreating OpenLIT setup from prose:

```python
from crewai_langfuse_demo.config import load_settings
from crewai_langfuse_demo.tracing import configure_tracing, flush_tracing

settings = load_settings()
configure_tracing(settings)

# Import modules that import CrewAI only after tracing is configured.
from crewai_langfuse_demo.basic.crew import build_crew

try:
    result = build_crew(settings).kickoff()
finally:
    flush_tracing()
```

The exact implementation is in `src/crewai_langfuse_demo/tracing.py`. It correctly builds the Langfuse Basic authorization header, uses the OTLP base endpoint, disables duplicate client instrumentors, disables message content, and instruments HTTPX/aiohttp for context propagation.

### 4. Route CrewAI model calls through LiteLLM Proxy

Use `src/crewai_langfuse_demo/llm.py` as the maintained reference. The Proxy host, key, and model come from `Settings`. Do not hardcode credentials.

### 5. Add the failure adapter only when needed

Use `FailureAdapter` for retry/fallback workflows that need a safe summary not retained by automatic telemetry. Follow `examples/failure_adapter_example.py` exactly. The public interface is:

- `FailureAdapter.install()`
- `FailureAdapter.complete(crew_completed=...)`
- `FailureAdapter.uninstall()`

### 6. Add the composite adapter only when needed

Use `CompositeToolAdapter.run_child(...)` for selected internal operations hidden inside a parent tool. Follow `examples/composite_tool_adapter_example.py` exactly. Do not wrap the parent tool because CrewAI already traces it.

## Development acceptance checklist

- [ ] One crew run, its automatic CrewAI observations, and its Proxy generations share one trace ID.
- [ ] The observed hierarchy is readable and no manual normal-operation spans duplicate automatic spans.
- [ ] Model calls appear as canonical Langfuse generations.
- [ ] Generation token and cost fields match the approved Proxy evidence source within documented rounding tolerance.
- [ ] HTTP transport observations are not counted as additional model generations.
- [ ] Automatic spans contain `kolibri.tenant.id`, `gen_ai.conversation.id`, `gen_ai.agent.id`, `kolibri.runtime.name = "crewai"`, and `kolibri.channel`.
- [ ] A fresh trace inspection confirms that prompts, completions, tool payloads, customer identifiers, raw errors, and stack traces are absent.
- [ ] Failed operations use low-cardinality `error.type` and OTel `ERROR` status.
- [ ] When enabled, the failure summary contains the exact `kolibri.failure.*` fields documented in the schema mapping.
- [ ] When enabled, composite child spans contain the exact `kolibri.composite.*` fields documented in the schema mapping.
- [ ] `.\scripts\run-tests.ps1` passes and a live healthy/failure run passes in the target environment.

`scripts/check-trace.ps1` prints a structural summary only. It does not independently prove privacy or cost parity; those require trace inspection and comparison with the approved Proxy record.
