# Troubleshooting

Run commands from the repository root, where `README.md` and `scripts/` are visible.

## Setup fails

Confirm Python 3.10–3.13 is installed:

```powershell
python --version
```

If PowerShell blocks local scripts, follow your organisation's policy. A process-only override, when approved, is:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then rerun `.\scripts\setup.ps1`.

## `.env` or a setting is missing

Create the ignored local file:

```powershell
Copy-Item .env.example .env
```

Provide approved Langfuse and Konecta LiteLLM Proxy values. Never paste keys into source, documentation, screenshots, issues, or commits.

## LiteLLM Proxy returns a connection or authentication error

- Confirm `LITELLM_PROXY_HOST`, `LITELLM_MASTER_KEY`, and `LITELLM_MODEL` match the approved development route.
- Obtain corrections through the normal secret-management and platform-support process.
- Do not print or share the key while troubleshooting.

This repository no longer starts a local Proxy. Historical local-Proxy files are available only in tag `archive-v3-local-proxy-2026-08-25`.

## Langfuse returns 401 or 403

Confirm `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` belong to the same project and that `LANGFUSE_BASE_URL` is correct.

## The run completes but no trace appears

1. Wait briefly and refresh Langfuse because telemetry is batched.
2. Open the project that owns the configured Langfuse keys.
3. Search for the service name in `OTEL_SERVICE_NAME`.
4. Confirm the approved LiteLLM Proxy route is reachable.
5. Do not add a second tracing library; it can create duplicate observations.

## Model generations appear in a separate trace

1. Rerun `.\scripts\setup.ps1` to install the documented HTTP instrumentors.
2. Confirm `configure_tracing()` runs before modules that import CrewAI workflows.
3. Ask the Proxy owner to confirm inbound W3C trace-context extraction is enabled.
4. Run a fresh scenario and verify the hierarchy again.

## Tests fail

```powershell
.\scripts\setup.ps1
.\scripts\run-tests.ps1
```

The tests do not call Langfuse or a model provider. If they still fail, share the non-secret error, Python version, and failing test name.

## Escalation information

Provide only:

- the script name;
- the sanitized error message;
- the Python version;
- whether the approved Proxy is reachable; and
- whether the failure is local tests, model routing, or trace export.

Never share `.env`, API keys, prompts, tool payloads, or customer data.
