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

## Folder map

This is the actual repository structure. The `src/crewai_langfuse_demo/` folder holds the code; the names below explain what each part is for.

```text
crewai-langfuse-tracing-demo/
|
|-- README.md                         # Start here.
|-- .env.example                      # Copy this to .env; never commit .env.
|-- .gitignore                        # Keeps .env and local files out of Git.
|-- requirements.txt                  # Python packages needed by the demo.
|
|-- scripts/
|   |-- setup.ps1                     # Installs the local Python environment.
|   |-- run-basic.ps1                 # Runs the basic automatic-tracing crew.
|   |-- run-retry.ps1                 # Runs retry + failure adapter.
|   |-- run-delegation.ps1            # Runs automatic delegation tracing.
|   |-- run-composite-tool.ps1        # Runs composite tool + composite adapter.
|   |-- check-trace.ps1               # Checks a Langfuse trace by its ID.
|   `-- open-langfuse.ps1             # Opens Langfuse in your default browser.
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
|   `-- github-publishing-checklist.md# How to keep a public copy safe.
|
`-- tests/
    `-- test_tools.py                 # Tests the fictional local tools.
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
