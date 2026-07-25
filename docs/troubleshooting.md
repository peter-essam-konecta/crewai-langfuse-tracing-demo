# Troubleshooting

Start with the exact error shown in PowerShell. The scripts stop early when a
required file, setting, or local environment is missing.

## Confirm you are in the repository root

The commands in the documentation assume the current folder contains
`README.md` and `scripts`.

```powershell
Test-Path .\README.md
Test-Path .\scripts\setup.ps1
```

Both commands should return `True`. If they return `False`, use `Set-Location`
to enter the cloned `crewai-langfuse-tracing-demo` folder.

## `python` is not recognized, or the Python version is unsupported

Check the installed version:

```powershell
python --version
```

Use Python 3.10, 3.11, 3.12, or 3.13. Install an approved version, close and
reopen PowerShell, then run `setup.ps1` again.

## PowerShell says script execution is disabled

Follow your organisation's PowerShell policy. If temporary process-level
permission is allowed, it affects only the current PowerShell window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then rerun the repository command. Do not change the machine-wide policy unless
your IT team instructs you to do so.

## A script says `.env` or a setting is missing

Create the local file if needed:

```powershell
Copy-Item .env.example .env
```

Then check the [settings table in Quick Start](quick-start.md#settings-by-proxy-option).
Do not paste credentials into source code, documentation, screenshots, issues,
or commits. The real `.env` file is intentionally ignored by Git.

## The Proxy test says connection refused

The Proxy is not listening at the URL in `LITELLM_PROXY_HOST`.

1. Start the chosen Proxy in a separate PowerShell window.
2. Leave that window open.
3. Confirm the port matches `.env`: `4000` for the normal local Proxy or `4002`
   for the V3 Cloud Proxy.
4. Run `test-litellm-proxy.ps1` again.

## Port 4000 or 4002 is already in use

Check which process is using the port:

```powershell
Get-NetTCPConnection -LocalPort 4000 -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 4002 -ErrorAction SilentlyContinue
```

Stop the old Proxy with `Ctrl+C` in its original window. Alternatively, start
the script with another `-Port` value and update `LITELLM_PROXY_HOST` to match.

## The Proxy returns 401 or 403

- Confirm `LITELLM_MASTER_KEY` in `.env` matches the selected Proxy.
- For an approved shared Proxy, obtain the correct URL and key through the
  normal secret-management process.
- Do not print or share the key while troubleshooting.

## Langfuse returns 401 or 403

Confirm that `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` belong to the same
Langfuse Cloud project and that `LANGFUSE_BASE_URL` is correct. Replace invalid
keys through the approved secret-management process.

## The CrewAI run completes but no trace appears

1. Wait a few seconds and refresh Langfuse; telemetry is sent in batches.
2. Open the project that owns the keys in `.env`.
3. Search for the service name in `OTEL_SERVICE_NAME`.
4. Confirm the Proxy window is still running.
5. Run `test-litellm-proxy.ps1` to verify the model route.
6. Check that `LANGFUSE_BASE_URL` does not point to the retired Docker setup.

Do not add another tracing library as a quick fix. A second instrumentor can
create duplicate model records.

## The model generation appears in a separate trace

Rerun both setup scripts so the documented HTTP and Proxy instrumentation is
installed, then restart the Proxy and run a fresh CrewAI scenario. Use the
repository start scripts; they load the settings needed to preserve the trace
connection across the local process boundary.

## `v3CostReady` is `false`

Check all of the following:

- `start-v3-cloud-proxy.ps1` is running, not the normal Proxy script.
- `LITELLM_PROXY_HOST` uses the same V3 Proxy port, normally `4002`.
- The trace ID belongs to a fresh run made through that V3 Proxy.
- The output reports at least one canonical generation.
- Every item in `checks` has `"Pass": true`.

The Langfuse public API cannot confirm OpenTelemetry `SpanKind`; that separate
message does not make `v3CostReady` false.

## Tests fail

Run the application setup again, then rerun the tests:

```powershell
.\scripts\setup.ps1
.\scripts\run-tests.ps1
```

The tests are local and do not need Groq or Langfuse credentials. If they still
fail, keep the full error text but remove any sensitive values before sharing it.

## Still blocked

When asking a developer for help, share:

- the script name;
- the non-secret error message;
- your Python version;
- whether you use an approved Proxy, normal local Proxy, or V3 Cloud Proxy; and
- whether the Proxy smoke test passed.

Never share `.env`, API keys, prompts, tool payloads, or real customer data.
