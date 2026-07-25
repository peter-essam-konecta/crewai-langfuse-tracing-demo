# PowerShell Scripts Reference

Run every command in this guide from the repository root, where `README.md` and
the `scripts` folder are visible.

You normally use the short scenario scripts such as `run-basic.ps1`. The shared
`run-example.ps1` script is included mainly so maintainers can see how all four
scenarios use the same setup.

## Recommended order

1. Copy `.env.example` to `.env` and add the approved values.
2. Run `setup.ps1` once.
3. Run `run-tests.ps1`.
4. Choose an existing Proxy, the normal local Proxy, or the V3 Cloud Proxy.
5. If using a local Proxy, start it in a separate PowerShell window and leave it running.
6. Run one CrewAI scenario.
7. Open Langfuse and inspect the new trace.
8. Use `check-trace.ps1`, or `inspect-v3-compliance.ps1` for the V3 route.

## Setup and test scripts

### `setup.ps1`

**Purpose:** Creates `.venv` and installs the packages used by the CrewAI demo.

**Use it:** Once after cloning, and again after `requirements.txt` changes.

**Needs:** Python 3.10, 3.11, 3.12, or 3.13.

```powershell
.\scripts\setup.ps1
```

**Success looks like:** The final line starts with `Setup complete`.

### `setup-litellm-proxy.ps1`

**Purpose:** Creates the separate `.proxy-venv` environment and installs the
full LiteLLM Proxy package. Keeping this separate avoids dependency conflicts
with CrewAI.

**Use it:** Only when running either local Proxy supplied by this repository.

```powershell
.\scripts\setup-litellm-proxy.ps1
```

**Success looks like:** The final line starts with `LiteLLM Proxy setup complete`.

### `run-tests.ps1`

**Purpose:** Runs the safe local unit tests for the fictional tools and V3 cost
mapper. It does not call Groq or send a trace to Langfuse.

**Needs:** `setup.ps1` must have completed.

```powershell
.\scripts\run-tests.ps1
```

**Success looks like:** The test output ends with `OK`.

## Proxy scripts

### `start-litellm-proxy.ps1`

**Purpose:** Starts the normal teaching Proxy on `127.0.0.1:4000`. It routes
`demo-groq` to the safe Groq demo model and sends canonical model telemetry to
Langfuse.

**Needs:** `setup-litellm-proxy.ps1` and the local-Proxy values in `.env`.

```powershell
.\scripts\start-litellm-proxy.ps1
```

The script keeps running. Leave its window open and press `Ctrl+C` to stop it.
You may choose another port with `-Port`, but `LITELLM_PROXY_HOST` in `.env`
must use the same port:

```powershell
.\scripts\start-litellm-proxy.ps1 -Port 4010
```

### `start-v3-cloud-proxy.ps1`

**Purpose:** Starts the optional V3 cost-validation Proxy on `127.0.0.1:4002`.
It adds `gen_ai.usage.cost` to the existing canonical generation and sends the
telemetry directly to Langfuse Cloud. It does not require Langfuse Docker.

**Needs:** `setup-litellm-proxy.ps1`, the local-Proxy values in `.env`, and
`LITELLM_PROXY_HOST=http://127.0.0.1:4002`.

```powershell
.\scripts\start-v3-cloud-proxy.ps1
```

This script also keeps running until you press `Ctrl+C`. Its optional `-Port`
parameter works like the normal Proxy port.

### `test-litellm-proxy.ps1`

**Purpose:** Sends one safe test request to the URL in `LITELLM_PROXY_HOST`.

**Needs:** The chosen Proxy must already be running, and
`LITELLM_MASTER_KEY` must match it.

```powershell
.\scripts\test-litellm-proxy.ps1
```

**Success looks like:** It prints `LiteLLM Proxy response` followed by a short
confirmation from the model.

## CrewAI scenario scripts

All four scripts below load `.env`, use the Python environment created by
`setup.ps1`, run one scenario, and flush pending telemetry before exiting.

### `run-basic.ps1`

Runs the simplest three-agent workflow with automatic tracing only.

```powershell
.\scripts\run-basic.ps1
```

### `run-retry.ps1`

Runs a controlled retry scenario and enables the safe failure adapter. The
trace should include one `demo.failure_summary` observation.

```powershell
.\scripts\run-retry.ps1
```

### `run-delegation.ps1`

Runs the coordinator and specialist delegation scenario. It relies on
automatic tracing and does not enable an adapter.

```powershell
.\scripts\run-delegation.ps1
```

### `run-composite-tool.ps1`

Runs a parent tool with two hidden child operations and enables the composite
adapter. The trace should include two `demo.composite.child.*` observations.

```powershell
.\scripts\run-composite-tool.ps1
```

### `run-example.ps1`

**Purpose:** Shared internal runner used by the four friendly scenario scripts.
Most users should not call it directly.

It accepts `-Scenario basic`, `retry`, `delegation`, or `composite-tool`. The
optional `-FailureAdapter` and `-CompositeAdapter` switches are deliberately
selected by the friendly scripts so the documented examples stay consistent.

Example equivalent to `run-basic.ps1`:

```powershell
.\scripts\run-example.ps1 -Scenario basic
```

## Langfuse helper scripts

### `open-langfuse.ps1`

**Purpose:** Opens the `LANGFUSE_BASE_URL` from `.env` in the default browser.

```powershell
.\scripts\open-langfuse.ps1
```

Open the newest trace for the service name in `OTEL_SERVICE_NAME`.

### `check-trace.ps1`

**Purpose:** Reads one trace through the Langfuse public API and prints a short
summary: root name, observation count, agents, tools, model generations, and
adapter observations.

**Needs:** Langfuse URL and keys in `.env`, plus a trace ID copied from Langfuse.

```powershell
.\scripts\check-trace.ps1 -TraceId <trace-id>
```

This is a helpful summary, not the formal V3 cost check.

### `inspect-v3-compliance.ps1`

**Purpose:** Checks the connected V3 Cloud trace for canonical generations,
matching Proxy requests, and matching `gen_ai.usage.cost` values.

```powershell
.\scripts\inspect-v3-compliance.ps1 -TraceId <trace-id>
```

**Success looks like:** `v3CostReady` is `true` and all four checks have
`"Pass": true`. OpenTelemetry `SpanKind` is listed separately because the
Langfuse public API does not expose it.

## If a script fails

Read [Troubleshooting](troubleshooting.md). The error messages intentionally
name the missing file, setting, environment, or service whenever possible.
