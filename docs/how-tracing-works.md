# How Tracing Works

The same tracing setup is used by every example in this repository.

```text
CrewAI example
  -> OpenLIT automatic tracing
  -> Langfuse

CrewAI model request
  -> LiteLLM Proxy
  -> canonical model generation in Langfuse
```

The starting code is [src/crewai_langfuse_demo/tracing.py](../src/crewai_langfuse_demo/tracing.py).

It is called before CrewAI is imported. That order matters: OpenLIT needs to start first so it can observe CrewAI's normal work.

The tracing setup does four simple things:

1. sends OpenTelemetry traces to Langfuse;
2. turns off message-content capture;
3. prevents CrewAI's separate hosted tracing from running beside OpenLIT; and
4. disables client-side LiteLLM/OpenAI tracing because the LiteLLM Proxy already owns the model-generation record.

The result is one connected trace without adding manual spans to ordinary crews, agents, tasks, or tools.

