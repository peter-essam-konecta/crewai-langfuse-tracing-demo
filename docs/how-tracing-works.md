# How Tracing Works

The same tracing setup is used by every example in this repository.

```text
CrewAI example
  -> OpenLIT automatic tracing
  -> Langfuse

CrewAI model request
  -> LiteLLM Proxy
  -> model provider

LiteLLM Proxy
  -> canonical model generation, tokens, latency, and cost in Langfuse
```

For the optional Cloud V3 cost-validation route, the Proxy adds
`gen_ai.usage.cost` to that same canonical model generation. It does not create
a second generation or a second cost. This route sends directly to Langfuse
Cloud through `LANGFUSE_BASE_URL`; it does not use Langfuse Docker.

The starting code is [src/crewai_langfuse_demo/tracing.py](../src/crewai_langfuse_demo/tracing.py).

It is called before CrewAI is imported. That order matters: OpenLIT needs to start first so it can observe CrewAI's normal work.

The tracing setup does four simple things:

1. sends OpenTelemetry traces to Langfuse;
2. turns off message-content capture;
3. prevents CrewAI's separate hosted tracing from running beside OpenLIT; and
4. disables client-side LiteLLM/OpenAI tracing because the LiteLLM Proxy already owns the model-generation record.

It also automatically forwards the workflow's trace connection through the
HTTP clients used to call the Proxy. That keeps the Proxy generation inside the
same CrewAI workflow trace without adding application-written spans.

The result is one connected trace without adding manual spans to ordinary crews, agents, tasks, or tools.

For a complete local learning setup, this repository includes an optional Proxy configuration and start script in [litellm-proxy/](../litellm-proxy/README.md). Developers who already have an approved development Proxy should use that instead.
