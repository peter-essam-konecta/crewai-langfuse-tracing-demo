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

4. In a separate PowerShell window, start the Proxy:

   ```powershell
   .\scripts\start-litellm-proxy.ps1
   ```

5. Leave that window open. In a second PowerShell window, test the Proxy:

   ```powershell
   .\scripts\test-litellm-proxy.ps1
   ```

6. Then run a CrewAI example, for example:

   ```powershell
   .\scripts\run-basic.ps1
   ```

The local Proxy binds to `127.0.0.1`, so it is available only on your own machine. Press `Ctrl+C` in the Proxy window to stop it.

