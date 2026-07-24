# CrewAI + Langfuse Tracing Demo

A small, safe teaching repository that shows how to trace a CrewAI workflow in Langfuse.

It contains two things:

1. A **basic crew** with automatic tracing only.
2. **Advanced crews** that show when a small reusable adapter is useful.

All customer-support data in this repository is fictional. Do not add real customer data, credentials, prompts, or tool payloads to the code or traces.

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

### 3. Run the basic crew

```powershell
.\scripts\run-basic.ps1
```

### 4. Open Langfuse

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
- [How to publish a safe copy on GitHub](docs/github-publishing-checklist.md)

