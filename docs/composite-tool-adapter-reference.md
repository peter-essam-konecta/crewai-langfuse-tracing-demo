# Composite-Tool Adapter Reference

Use this adapter when one CrewAI parent tool runs important internal child operations that automatic tracing does not show in Langfuse.

## The problem it solves

Automatic CrewAI tracing normally shows the parent tool called by the agent. If that parent tool calls internal helper functions or child tools, those internal operations may be hidden.

The composite-tool adapter adds only the selected child operations. It does not replace automatic tracing of the crew, agents, tasks, parent tool, or model calls.

## The two files to open

| What you want to see | File |
| --- | --- |
| The reusable adapter itself | [composite_tool.py](../src/crewai_langfuse_demo/adapters/composite_tool.py) |
| The smallest integration example | [composite_tool_adapter_example.py](../examples/composite_tool_adapter_example.py) |

## Step by step: how to add it

1. Import `CompositeToolAdapter` in the parent-tool module.
2. Create one adapter instance.
3. Identify the internal child operations that must be reviewable.
4. Wrap each selected operation with `adapter.run_child(...)`.
5. Give the adapter a safe parent-tool name and child-operation name.
6. Keep arguments, returned content, prompts, and raw errors out of adapter attributes.

The complete minimal code is in [composite_tool_adapter_example.py](../examples/composite_tool_adapter_example.py).

## What it adds to Langfuse

For each wrapped child operation, it creates one `demo.composite.child.*` observation with:

- parent tool name;
- child-operation name; and
- final outcome: `succeeded` or `failed`.

## When to use it

Use it only when the hidden child operations matter for support, audit, reliability, or cost review. It is not needed for ordinary one-step tools.

## Does it work automatically for every new tool?

No. The adapter is reusable unchanged, but the developer must explicitly wrap the internal child operations that should appear in Langfuse. It cannot discover those hidden functions automatically.

