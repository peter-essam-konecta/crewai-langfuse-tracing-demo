# What You See in Langfuse

After each example completes, open the newest trace in Langfuse.

| Example | What should be visible | Extra adapter observation |
| --- | --- | --- |
| Basic | Workflow, three agents, three tasks, three tools, model generations | None |
| Retry | Workflow, retry-aware agent, retryable tool, model generations | `demo.failure_summary` |
| Delegation | Coordinator, policy specialist, delegation work, policy tool, model generations | None |
| Composite tool | Parent tool, model generations | `demo.composite.child.*` for the two internal child operations |

Two records can look similar:

- a model generation is the model call to count for usage and cost; and
- a LiteLLM Proxy HTTP record is useful transport information.

Do not count both as two model calls for the same request.

## Optional Cloud V3 cost check

When you run the optional V3 Cloud Proxy, each canonical `chat demo-groq`
generation should have `gen_ai.usage.cost`. That value should match LiteLLM's
existing `litellm.cost.total` value. Run
`.\scripts\inspect-v3-compliance.ps1 -TraceId <trace-id>` to check this without
copying trace data into the repository.

## Safe data rule

This repository keeps message content capture off. If you see prompts, responses, tool arguments, tool results, raw exceptions, or real customer data in a trace, stop and review the configuration before sharing the trace.
