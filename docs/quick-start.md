# Quick Start

This page is the shortest path from an empty machine to a visible Langfuse trace.

## Before you begin

You need:

- Python installed;
- approved Langfuse keys;
- either access to an approved LiteLLM Proxy route **or** a Groq key for the optional local Proxy; and
- PowerShell on Windows.

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

4. Choose one Proxy path:

   - **Existing approved Proxy:** set its URL and key in `.env`, then continue to step 5.
   - **Optional local Proxy:** add `GROQ_API_KEY` to `.env`, open a second PowerShell window, and run:

     ```powershell
     .\scripts\start-litellm-proxy.ps1
     ```

     Leave it running. In another window, confirm it works:

     ```powershell
     .\scripts\test-litellm-proxy.ps1
     ```

     Read [the local Proxy guide](../litellm-proxy/README.md) if you need more detail.

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
