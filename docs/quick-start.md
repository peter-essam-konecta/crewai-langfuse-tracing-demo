# Quick Start

This page is the shortest path from an empty machine to a visible Langfuse trace.

## Before you begin

You need:

- Git installed if you still need to clone the repository;
- Python 3.10, 3.11, 3.12, or 3.13;
- approved Langfuse keys;
- either access to an approved LiteLLM Proxy route **or** a Groq key for the optional local Proxy; and
- PowerShell on Windows.

## Open the repository root

If you have not cloned the repository yet:

```powershell
git clone https://github.com/peter-essam-konecta/crewai-langfuse-tracing-demo.git
Set-Location crewai-langfuse-tracing-demo
```

If it is already cloned, open PowerShell in that folder. Confirm that you are
in the correct place:

```powershell
python --version
Test-Path .\scripts\setup.ps1
```

The Python version must be 3.10 through 3.13, and `Test-Path` should return
`True`.

## Settings by Proxy option

Copy `.env.example` to `.env`, then use this table to understand which values
are required. Keep all real values out of Git.

| Setting | Existing approved Proxy | Normal local Proxy | V3 Cloud Proxy |
| --- | --- | --- | --- |
| `LANGFUSE_BASE_URL` | Required | Required | Required; use the Cloud URL |
| `LANGFUSE_PUBLIC_KEY` | Required | Required | Required |
| `LANGFUSE_SECRET_KEY` | Required | Required | Required |
| `LITELLM_PROXY_HOST` | Approved Proxy URL | `http://127.0.0.1:4000` | `http://127.0.0.1:4002` |
| `LITELLM_MASTER_KEY` | Required | Required | Required |
| `GROQ_API_KEY` | Not required for this option | Required | Required |

The safe `OTEL_SERVICE_NAME`, `DEMO_TENANT_ID`, and `DEMO_CONVERSATION_ID`
defaults may remain unchanged for the teaching demo.

## Steps

1. Copy the example settings file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Put the approved settings into `.env`. Do not commit this file.

3. Install the local Python environment:

   ```powershell
   .\scripts\setup.ps1
   ```

   Then run the local tests:

   ```powershell
   .\scripts\run-tests.ps1
   ```

   A successful test run ends with `OK`. It does not call Groq or Langfuse.

4. Choose one Proxy path:

   - **Existing approved Proxy:** set its URL and key in `.env`, then continue to step 5.
   - **Optional local Proxy:** add `GROQ_API_KEY` to `.env`, open a second PowerShell window, and run:

     ```powershell
     .\scripts\setup-litellm-proxy.ps1
     .\scripts\start-litellm-proxy.ps1
     ```

     Leave it running. In another window, confirm it works:

     ```powershell
     .\scripts\test-litellm-proxy.ps1
     ```

     Read [the local Proxy guide](../litellm-proxy/README.md) if you need more detail.

   - **Optional Cloud V3 cost check:** set `LITELLM_PROXY_HOST=http://127.0.0.1:4002` in your ignored `.env`, then start this separate local Proxy:

     ```powershell
     .\scripts\setup-litellm-proxy.ps1
     .\scripts\start-v3-cloud-proxy.ps1
     ```

     This uses the `LANGFUSE_BASE_URL` Cloud address from `.env`; no Langfuse Docker setup is needed. After the CrewAI run, validate the trace cost with:

     ```powershell
     .\scripts\inspect-v3-compliance.ps1 -TraceId <trace-id>
     ```

5. Run the simplest CrewAI example:

   ```powershell
   .\scripts\run-basic.ps1
   ```

6. Open Langfuse:

   ```powershell
   .\scripts\open-langfuse.ps1
   ```

7. Open the newest trace for `crewai-langfuse-tracing-demo`. You should see the workflow, its agents and tasks, named tools, and model generations.

If you do not see a trace, first check that the LiteLLM Proxy and the Langfuse URL in `.env` are correct. Do not add another tracing library to “fix” it; that can create duplicate data.

For details about any command, read the [PowerShell scripts reference](scripts-reference.md).
For common errors, read [Troubleshooting](troubleshooting.md).
