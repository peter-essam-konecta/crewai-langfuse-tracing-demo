# Failure Adapter Reference

Use this adapter when a CrewAI trace must clearly show **which tool failed, the safe error category, retry count, and final outcome**.

## The problem it solves

CrewAI detects tool failures automatically. However, automatic tracing can export only generic error records. A reviewer may not be able to tell which tool failed or whether the crew recovered.

The failure adapter adds one small, safe summary only when a tool fails. It does not add normal crew, agent, task, tool, or model spans.

## The two files to open

| What you want to see | File |
| --- | --- |
| The reusable adapter itself | [failure.py](../src/crewai_langfuse_demo/adapters/failure.py) |
| The smallest integration example | [failure_adapter_example.py](../examples/failure_adapter_example.py) |

## Step by step: how to add it

1. Import `FailureAdapter` in the file that starts your crew.
2. Create one adapter before `crew.kickoff()`.
3. Call `install()` once. It listens to existing CrewAI tool events.
4. Run the crew normally with `crew.kickoff()`.
5. Call `complete()` with the crew result. If the crew failed, call it with `False` in the exception path.
6. Call `uninstall()` in `finally` so the listeners do not remain active for another run.

The complete minimal code is in [failure_adapter_example.py](../examples/failure_adapter_example.py).

## What it adds to Langfuse

Only when a tool fails, it creates one `demo.failure_summary` observation with:

- failed tool name;
- safe error type;
- retry count; and
- final outcome: `retry_succeeded`, `fallback_completed`, or `aborted`.

It does **not** export tool arguments, prompts, responses, raw exception text, or stack traces.

## When to use it

Use it when readable failure or retry information is required. Do not add it merely because a crew exists; automatic tracing is enough for a normal healthy crew.

## When the adapter code needs a change

The adapter is normally reused unchanged. Change it only when the crew needs a new **approved safe error category** that is not already handled by the allow-list.

