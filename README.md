# CrewAI + Langfuse Tracing Reference

A focused Task 005 reference showing how a CrewAI application sends automatic workflow telemetry to Langfuse while routing model calls through Konecta's LiteLLM Proxy.

> AI coding agents must start with [`AGENTS.md`](AGENTS.md). This is an R&D and developer-handoff reference, not a production deployment.

## The pattern

```text
CrewAI + OpenLIT
  -> automatic workflow, agent, task, and tool telemetry
  -> Langfuse

CrewAI model request
  -> Konecta LiteLLM Proxy
  -> canonical generation, tokens, latency, and cost
  -> Langfuse in the same trace
```

Start with automatic tracing. Add `FailureAdapter` only for failure/retry summaries and `CompositeToolAdapter` only for important child operations hidden inside a parent tool. Delegation needs no adapter.

## Run locally

Use PowerShell and Python 3.10–3.13:

```powershell
git clone https://github.com/peter-essam-konecta/crewai-langfuse-tracing-demo.git
Set-Location crewai-langfuse-tracing-demo
Copy-Item .env.example .env
```

Fill `.env` with approved Langfuse and Konecta LiteLLM Proxy values through the normal secret-management process. Never commit `.env`.

```powershell
.\scripts\setup.ps1
.\scripts\run-tests.ps1
.\scripts\run-basic.ps1
.\scripts\open-langfuse.ps1
```

## Scenarios

| Scenario | Command | Tracing approach |
| :--- | :--- | :--- |
| Basic workflow | `.\scripts\run-basic.ps1` | Automatic only |
| Retry/failure | `.\scripts\run-retry.ps1` | Automatic + failure adapter |
| Delegation | `.\scripts\run-delegation.ps1` | Automatic only |
| Composite tool | `.\scripts\run-composite-tool.ps1` | Automatic + composite adapter |

Inspect a recorded trace without copying its payload into the repository:

```powershell
.\scripts\check-trace.ps1 `
  -TraceId <RETRY_TRACE_ID> `
  -ExpectedTool lookup_retryable_order_status `
  -RequireFailureSummary
```

The checker runs eleven schema-derived structural checks, uses Final Trace Schema tool attributes before its explicit legacy fallback, and returns a failing exit code when required structure is missing. It does not claim privacy or cost proof, and it validates SpanKind only when the Langfuse API exposes it.

## Source of truth

| Document | Use it for |
| :--- | :--- |
| [`AGENTS.md`](AGENTS.md) | AI-agent rules, reading order, and invariants |
| [Schema contract](docs/trace-schema-contract.md) | Exact application and adapter attributes |
| [Developer guide](docs/developer-guide.md) | Dependency review, implementation, and acceptance checklist |
| [Evidence](docs/trace-verification-and-evidence.md) | Recorded live trace claims and scenario map |
| [Architecture decisions](docs/architecture-decisions-and-faq.md) | Why OpenLIT and narrowly scoped adapters were selected |
| [Implementation handoff](docs/implementation-handoff.md) | R&D, development, and approval ownership |
| [Troubleshooting](docs/troubleshooting.md) | Common setup and connected-trace failures |

The maintained implementation is under `src/`, minimal adapter examples are under `examples/`, scenario commands are under `scripts/`, and regression coverage is under `tests/`.

## Historical material

The previous local-Groq Proxy and V3-era cost-reproduction paths were removed from `main` to keep the enterprise handoff direct. They remain available in tag `archive-v3-local-proxy-2026-08-25` for audit and historical reproduction.
