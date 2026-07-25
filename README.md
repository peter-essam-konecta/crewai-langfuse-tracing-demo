# CrewAI + Langfuse Tracing Demo

A small, safe teaching repository that shows how to trace a CrewAI workflow in Langfuse.

It contains two things:

1. A **basic crew** with automatic tracing only.
2. **Advanced crews** that show when a small reusable adapter is useful.

All customer-support data in this repository is fictional. Do not add real customer data, credentials, prompts, or tool payloads to the code or traces.

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

## Adapter references

| If you need to understand… | Open this explanation | Open this simple Python code |
| --- | --- | --- |
| A failed tool or retry outcome | [Failure adapter reference](docs/failure-adapter-reference.md) | [failure_adapter_example.py](examples/failure_adapter_example.py) |
| Hidden child operations inside a parent tool | [Composite-tool adapter reference](docs/composite-tool-adapter-reference.md) | [composite_tool_adapter_example.py](examples/composite_tool_adapter_example.py) |

## Folder map

This is the actual repository structure. The `src/crewai_langfuse_demo/` folder holds the code; the names below explain what each part is for.

```text
crewai-langfuse-tracing-demo/
|
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
|   |-- run-basic.ps1                 # Runs the basic automatic-tracing crew.
|   |-- run-retry.ps1                 # Runs retry + failure adapter.
|   |-- run-delegation.ps1            # Runs automatic delegation tracing.
|   |-- run-composite-tool.ps1        # Runs composite tool + composite adapter.
|   |-- check-trace.ps1               # Checks a Langfuse trace by its ID.
|   |-- open-langfuse.ps1             # Opens Langfuse in your default browser.
|   |-- start-litellm-proxy.ps1       # Starts the optional local LiteLLM Proxy.
|   |-- start-v3-cloud-proxy.ps1      # Starts the optional V3 cost-validation Proxy.
|   |-- inspect-v3-compliance.ps1     # Checks V3 cost fields in a Langfuse trace.
|   `-- test-litellm-proxy.ps1        # Sends a safe Proxy smoke test.
|
|-- litellm-proxy/
|   |-- config.yaml                   # Safe local demo route: demo-groq.
|   |-- config.v3-cloud.yaml          # Separate Cloud V3 cost-validation route.
|   |-- v3_cost_mapper.py             # Adds V3 cost to the canonical generation.
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
|   |-- quick-start.md                # Full beginner setup guide.
|   |-- how-tracing-works.md          # How CrewAI, LiteLLM, and Langfuse connect.
|   |-- how-adapters-work.md          # When and how to use each adapter.
|   |-- what-you-see-in-langfuse.md   # What to expect after each run.
|   |-- failure-adapter-reference.md  # Full failure-adapter explanation.
|   `-- composite-tool-adapter-reference.md # Full composite-adapter explanation.
|
`-- tests/
    |-- test_tools.py                 # Tests the fictional local tools.
    `-- test_litellm_v3_cost_mapper.py # Tests the optional V3 cost mapping.
```

## Start here

### 1. Prepare your local settings

```powershell
Copy-Item .env.example .env
```

Open `.env` and fill in the approved Langfuse and LiteLLM values supplied through your normal secret-management process. Do not commit `.env`.

### 2. Install the demo

```powershell
.\scripts\setup.ps1
```

### 3. Choose your LiteLLM Proxy

**Option A — use an approved existing Proxy:** set `LITELLM_PROXY_HOST` and `LITELLM_MASTER_KEY` in `.env`, then continue to step 4.

**Option B — start the optional local Proxy:** add `GROQ_API_KEY` to `.env`, then open a separate PowerShell window and run:

```powershell
.\scripts\setup-litellm-proxy.ps1
.\scripts\start-litellm-proxy.ps1
```

Leave that window open. In a second window, verify the Proxy before running CrewAI:

```powershell
.\scripts\test-litellm-proxy.ps1
```

See [the local Proxy guide](litellm-proxy/README.md) for the full explanation.

**Option C — validate V3 cost with Langfuse Cloud:** this is an optional, separate local Proxy for checking the final cost field used by the V3 schema. Set `LITELLM_PROXY_HOST=http://127.0.0.1:4002` in your ignored `.env`, then run:

```powershell
.\scripts\setup-litellm-proxy.ps1
.\scripts\start-v3-cloud-proxy.ps1
```

Run the basic crew, copy its trace ID from Langfuse Cloud, and check it with:

```powershell
.\scripts\inspect-v3-compliance.ps1 -TraceId <trace-id>
```

This option does not require Langfuse Docker. It sends telemetry directly to the Cloud URL in `LANGFUSE_BASE_URL`.

### 4. Run the basic crew

```powershell
.\scripts\run-basic.ps1
```

### 5. Open Langfuse

```powershell
.\scripts\open-langfuse.ps1
```

Open the newest trace. A successful basic run should show one connected workflow with agents, tasks, named tools, and model generations.

## Run the advanced examples

| Goal | Command | Adapter used? |
| --- | --- | --- |
| Show a normal crew | `.\scripts\run-basic.ps1` | No. Automatic tracing only. |
| Show a retry and readable failure summary | `.\scripts\run-retry.ps1` | Yes. Failure adapter. |
| Show agent delegation | `.\scripts\run-delegation.ps1` | No. Automatic tracing only. |
| Show hidden child operations inside one parent tool | `.\scripts\run-composite-tool.ps1` | Yes. Composite-tool adapter. |

## How the code is organised

```text
src/crewai_langfuse_demo/
|-- tracing.py                 # Starts automatic OpenLIT tracing once.
|-- adapters/
|   |-- failure.py             # Adds a safe summary only when a tool fails.
|   `-- composite_tool.py      # Adds safe child-operation observations when needed.
|-- basic/                     # Simple three-agent support crew.
`-- advanced/                  # Retry, delegation, and composite-tool crews.
```

The normal crew code does not create custom spans. The adapters are explicit exceptions for gaps demonstrated by the advanced examples. Read [how adapters work](docs/how-adapters-work.md) before changing them.

## Quick “did it work?” check

After a run finishes, open Langfuse and inspect the newest trace for this service. Check that it has:

- one workflow trace;
- the named agents and tasks for the selected example;
- named tools; and
- model generations from the LiteLLM route.

For a deeper check, copy the trace ID from Langfuse and run:

```powershell
.\scripts\check-trace.ps1 -TraceId <trace-id>
```

## More help

- [Quick start](docs/quick-start.md)
- [How tracing works](docs/how-tracing-works.md)
- [How adapters work](docs/how-adapters-work.md)
- [What to expect in Langfuse](docs/what-you-see-in-langfuse.md)
- [Failure adapter reference](docs/failure-adapter-reference.md)
- [Composite-tool adapter reference](docs/composite-tool-adapter-reference.md)
- [Optional local LiteLLM Proxy](litellm-proxy/README.md)
