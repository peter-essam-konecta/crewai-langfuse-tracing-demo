# Quick Start

This page is the shortest path from an empty machine to a visible Langfuse trace.

## Before you begin

You need:

- Python installed;
- approved Langfuse keys;
- access to an approved LiteLLM Proxy route; and
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

4. Run the simplest example:

   ```powershell
   .\scripts\run-basic.ps1
   ```

5. Open Langfuse:

   ```powershell
   .\scripts\open-langfuse.ps1
   ```

6. Open the newest trace for `crewai-langfuse-tracing-demo`. You should see the workflow, its agents and tasks, named tools, and model generations.

If you do not see a trace, first check that the LiteLLM Proxy and the Langfuse URL in `.env` are correct. Do not add another tracing library to “fix” it; that can create duplicate data.

