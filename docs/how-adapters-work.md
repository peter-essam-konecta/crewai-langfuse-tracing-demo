# How the Adapters Work

Adapters are not the default. Start with automatic CrewAI tracing. Add an adapter only when the automatic trace has a real visibility gap.

## 1. Failure adapter: retry example

The retry example fails the same fictional tool twice and then succeeds. CrewAI detects those failures automatically, but the automatic export may not make the failed tool and recovery story readable enough in Langfuse.

The runner makes the relationship explicit:

```text
retry example
  + automatic tracing
  + FailureAdapter installed once around crew.kickoff()
  = normal trace plus one safe failure summary
```

The code is in [failure.py](../src/crewai_langfuse_demo/adapters/failure.py). It exports only:

- tool name;
- safe error category;
- retry count; and
- final outcome.

It never exports tool arguments, prompts, responses, raw errors, or stack traces.

Run it with:

```powershell
.\scripts\run-retry.ps1
```

## 2. Composite-tool adapter: composite example

The composite example calls one parent tool. That parent tool runs two internal child operations. Automatic tracing normally shows the parent tool but may not show those child operations.

```text
composite-tool example
  + automatic tracing of the parent tool
  + CompositeToolAdapter around each important child operation
  = parent tool plus safe child-operation observations
```

The code is in [composite_tool.py](../src/crewai_langfuse_demo/adapters/composite_tool.py). It exports the parent-tool name, child-operation name, and safe final outcome only.

Run it with:

```powershell
.\scripts\run-composite-tool.ps1
```

## 3. Delegation: no adapter

The delegation example is deliberately automatic-only. Its trace should show the coordinator, specialist, and handoff. Do not add an adapter merely to create more normal-operation spans.

```powershell
.\scripts\run-delegation.ps1
```

