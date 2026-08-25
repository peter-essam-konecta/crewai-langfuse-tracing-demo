# CrewAI + Langfuse Tracing Demo

A small, safe reference repository that shows how to trace a CrewAI workflow in Langfuse using LiteLLM Proxy and OpenLIT.

> **AI coding agents and developers:** Start with [**`AGENTS.md`**](AGENTS.md). It is the canonical Task 005 R&D and developer-handoff entry point. The repository is a tested reference, not a production deployment or a substitute for target-environment validation.

---

## Understand this repository in 20 seconds

```text
Basic use case
  -> uses automatic tracing only

Retry failure
  -> uses automatic tracing + failure adapter

Delegation
  -> uses automatic tracing only

Composite/nested tool
  -> uses automatic tracing + composite adapter
```

The simple rule is: **start with automatic tracing**. Use an adapter only when the advanced example proves that automatic tracing cannot show an important part of the workflow clearly.

---

## Documentation & Architecture Index

| Category | Document | Description |
| :--- | :--- | :--- |
| **AI Entry Point** | [**`AGENTS.md`**](AGENTS.md) | Reading order, precedence rules, tested interfaces, and anti-patterns. |
| **Schema Mapping** | [**Trace Schema Mapping**](docs/trace-schema-contract.md) | Repository-owned CrewAI subset and code mapping to the approved Final Trace Schema. |
| **Developer Guide** | [**Developer Integration Guide**](docs/developer-guide.md) | 6-step production integration recipe & 11-point acceptance checklist. |
| **Architecture & FAQ** | [**Architecture Decisions & FAQ**](docs/architecture-decisions-and-faq.md) | OpenLIT vs OpenInference/OpenLLMetry comparison & Ticket #65 Q&A. |
| **Governance & Handoff** | [**Implementation Handoff**](docs/implementation-handoff.md) | Role boundaries between Incubation R&D (Peter) and Dev Team (Marwan). |
| **Live Trace Evidence** | [**Trace Verification & Evidence**](docs/trace-verification-and-evidence.md) | Live Langfuse Cloud trace links, trace IDs, and visual hierarchy trees. |
| **Adapters Reference** | [Failure Adapter](docs/failure-adapter-reference.md) / [Composite Tool](docs/composite-tool-adapter-reference.md) | Deep dives into safe failure summaries and child operations. |

---

## Folder Map

```text
crewai-langfuse-tracing-demo/
|-- AGENTS.md                         # Master AI instructions & SSOT.
|-- README.md                         # Start here.
|-- .env.example                      # Copy this to .env; never commit .env.
|-- .gitignore                        # Keeps .env and local files out of Git.
|-- requirements.txt                  # Python packages needed by the demo.
|-- requirements-proxy.txt            # Separate packages needed by local Proxy modes.
|
|-- examples/
|   |-- failure_adapter_example.py    # Smallest failure-adapter integration.
|   `-- composite_tool_adapter_example.py # Smallest composite-adapter integration.
|
|-- scripts/
|   |-- setup.ps1                     # Installs the local Python environment.
|   |-- setup-litellm-proxy.ps1       # Installs the separate local Proxy environment.
|   |-- run-tests.ps1                 # Runs the safe local unit tests.
|   |-- run-example.ps1               # Shared runner behind the scenario scripts.
|   |-- run-basic.ps1                 # Runs the basic automatic-tracing crew.
|   |-- run-retry.ps1                 # Runs retry + failure adapter.
|   |-- run-delegation.ps1            # Runs automatic delegation tracing.
|   |-- run-composite-tool.ps1        # Runs composite tool + composite adapter.
|   |-- check-trace.ps1               # Checks a Langfuse trace by its ID.
|   |-- open-langfuse.ps1             # Opens Langfuse in your default browser.
|   |-- start-litellm-proxy.ps1       # Starts the optional local LiteLLM Proxy.
|   |-- start-v3-cloud-proxy.ps1      # Starts the optional historical V3-era cost route.
|   |-- inspect-v3-compliance.ps1     # Checks that retained V3-era cost route.
|   `-- test-litellm-proxy.ps1        # Sends a safe Proxy smoke test.
|
|-- litellm-proxy/
|   |-- config.yaml                   # Safe local demo route.
|   |-- config.v3-cloud.yaml          # Retained historical V3-era cost route.
|   |-- v3_cost_mapper.py             # Adds cost to that route's canonical generation.
|   `-- README.md                     # Local Proxy setup, explained step by step.
|
|-- src/crewai_langfuse_demo/
|   |-- tracing.py                    # Starts automatic OpenLIT tracing once.
|   |-- adapters/
|   |   |-- failure.py                # Safe failure and retry summary adapter.
|   |   `-- composite_tool.py         # Safe child-operation adapter.
|   |-- basic/
|   |   |-- crew.py                   # Basic CrewAI use case.
|   |   `-- tools.py                  # Basic fictional local tools.
|   `-- advanced/
|       |-- crews.py                  # Retry, delegation, and composite crews.
|       `-- tools.py                  # Advanced fictional local tools.
|
|-- docs/
|   |-- trace-schema-contract.md      # CrewAI mapping to the approved final contract.
|   |-- developer-guide.md            # Production developer guide & acceptance checklist.
|   |-- architecture-decisions-and-faq.md # ADRs, benchmarks & Ticket #65 Q&A.
|   |-- implementation-handoff.md     # Governance & ownership matrix.
|   |-- trace-verification-and-evidence.md # Live trace links & visual trees.
|   |-- quick-start.md                # Full beginner setup guide.
|   |-- how-tracing-works.md          # How CrewAI, LiteLLM, and Langfuse connect.
|   |-- how-adapters-work.md          # When and how to use each adapter.
|   |-- what-you-see-in-langfuse.md   # What to expect after each run.
|   |-- scripts-reference.md          # Purpose, inputs, and output of every script.
|   |-- troubleshooting.md            # Common setup and tracing problems.
|   |-- failure-adapter-reference.md  # Full failure-adapter explanation.
|   `-- composite-tool-adapter-reference.md # Full composite-adapter explanation.
|
`-- tests/
    |-- test_tools.py                 # Tests the fictional local tools.
    |-- test_adapters.py              # Tests exact adapter spans and safe error mapping.
    |-- test_repository_contract.py   # Prevents documentation/code drift.
    `-- test_litellm_v3_cost_mapper.py # Tests the retained V3-era cost route.
```

---

## Start Here

Use Windows PowerShell and Python 3.10, 3.11, 3.12, or 3.13. Run every command from the cloned repository root:

```powershell
git clone https://github.com/peter-essam-konecta/crewai-langfuse-tracing-demo.git
Set-Location crewai-langfuse-tracing-demo
python --version
```

For a completely guided setup, use the [Quick Start](docs/quick-start.md).

### 1. Prepare your local settings

```powershell
Copy-Item .env.example .env
```

Open `.env` and fill in the approved Langfuse and LiteLLM values supplied through your normal secret-management process. Do not commit `.env`.

### 2. Install the demo

```powershell
.\scripts\setup.ps1
```

Confirm the local code is healthy before calling any external service:

```powershell
.\scripts\run-tests.ps1
```

### 3. Choose your LiteLLM Proxy

- **Option A — Use an approved existing Proxy:** set `LITELLM_PROXY_HOST` and `LITELLM_MASTER_KEY` in `.env`, then continue to step 4.
- **Option B — Start the optional local Proxy:** add `GROQ_API_KEY` to `.env`, then run `.\scripts\start-litellm-proxy.ps1` in a separate window.
- **Option C — Reproduce the retained historical V3-era cost route:** see [litellm-proxy/README.md](litellm-proxy/README.md). The current implementation contract is the approved final schema mapping, not the historical V3 draft.

### 4. Run the basic crew

```powershell
.\scripts\run-basic.ps1
```

### 5. Open Langfuse

```powershell
.\scripts\open-langfuse.ps1
```

---

## Run the advanced examples

| Goal | Command | Adapter used? |
| :--- | :--- | :--- |
| Show a normal crew | `.\scripts\run-basic.ps1` | No. Automatic tracing only. |
| Show a retry and readable failure summary | `.\scripts\run-retry.ps1` | Yes. Failure adapter. |
| Show agent delegation | `.\scripts\run-delegation.ps1` | No. Automatic tracing only. |
| Show hidden child operations inside one parent tool | `.\scripts\run-composite-tool.ps1` | Yes. Composite-tool adapter. |

---

## Quick “did it work?” check

After a run finishes, open Langfuse and inspect the newest trace. For a deeper check, copy the trace ID from Langfuse and run:

```powershell
.\scripts\check-trace.ps1 -TraceId <trace-id>
```
