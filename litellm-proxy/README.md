# Optional Local LiteLLM Proxy

Use this folder only when you need to run the complete teaching demo on your own machine.

If your team already provides an approved LiteLLM Proxy, do **not** start another one. Put the approved Proxy URL and key in `.env`, then go straight to the CrewAI run scripts.

## What this Proxy does

```text
CrewAI
  -> local LiteLLM Proxy at http://localhost:4000
  -> Groq model provider

local LiteLLM Proxy
  -> Langfuse model generations, tokens, latency, and cost
```

The Proxy exposes one model route:

```text
demo-groq -> groq/llama-3.3-70b-versatile
```

The CrewAI examples already use `demo-groq`, so no code changes are needed.

## Run it

1. Copy `.env.example` to `.env` in the repository root.
2. Set `GROQ_API_KEY`, `LITELLM_MASTER_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_SECRET_KEY` in `.env`.
3. Run the normal repository setup once:

   ```powershell
   .\scripts\setup.ps1
   ```

4. Set up the separate local Proxy environment. This avoids a known dependency conflict between CrewAI and the full LiteLLM Proxy package:

   ```powershell
   .\scripts\setup-litellm-proxy.ps1
   ```

5. In a separate PowerShell window, start the Proxy:

   ```powershell
   .\scripts\start-litellm-proxy.ps1
   ```

6. Leave that window open. In a second PowerShell window, test the Proxy:

   ```powershell
   .\scripts\test-litellm-proxy.ps1
   ```

7. Then run a CrewAI example, for example:

   ```powershell
   .\scripts\run-basic.ps1
   ```

The local Proxy binds to `127.0.0.1`, so it is available only on your own machine. Press `Ctrl+C` in the Proxy window to stop it.

## Optional: validate the Cloud V3 cost field

The normal Proxy above remains the default teaching route. Use this separate option only when you need to verify that Langfuse Cloud receives the V3 cost field on the real model generation.

1. Make sure `LANGFUSE_BASE_URL` is your Langfuse Cloud address in `.env`.
2. Temporarily set `LITELLM_PROXY_HOST=http://127.0.0.1:4002` in your ignored `.env`.
3. Start the separate Proxy:

   ```powershell
   .\scripts\setup-litellm-proxy.ps1
   .\scripts\start-v3-cloud-proxy.ps1
   ```

4. Run the basic crew, then copy the trace ID from Langfuse Cloud.
5. Check the result:

   ```powershell
   .\scripts\inspect-v3-compliance.ps1 -TraceId <trace-id>
   ```

The result is successful when `v3CostReady` is `true`. The check confirms that every canonical model generation has `gen_ai.usage.cost` and that it matches LiteLLM's calculated total cost. No Langfuse Docker container is involved.
