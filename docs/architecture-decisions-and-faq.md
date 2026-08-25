# Architecture Decisions & Technical FAQ (Ticket #65)

> **Status:** Reference document detailing architectural decisions, tool evaluation benchmarks, and empirical answers to GitHub Issue #65 questions.

---

## 1. Instrumentation Evaluation: Why OpenLIT?

During the Task 005 R&D investigation, three leading OpenTelemetry instrumentation frameworks were evaluated against the exact same CrewAI customer-support workflow, LiteLLM Proxy route, and Langfuse destination:

| Instrumentation Library | CrewAI Workflow Visible | Connected to LiteLLM in 1 Trace | Message Privacy Control | Evaluation Outcome |
| :--- | :---: | :---: | :---: | :--- |
| **OpenLIT `1.44.0`** | **Yes** (Crew, Agent, Task, Tool) | **Yes** (Single Connected Trace) | **Yes** (`capture_message_content=False`) | **Selected Standard Baseline** |
| **OpenInference CrewAI `1.1.10`** | Yes | **No** (Proxy calls split into separate traces) | Truncated prompts leaked by default | Rejected |
| **OpenLLMetry CrewAI `0.62.1`** | Yes | **No** (Proxy calls split into separate traces) | Prompts and completions exposed | Rejected |

### Key Takeaway
OpenLIT is the **only framework that maintains OpenTelemetry context propagation across the HTTP requests to the LiteLLM Proxy**, keeping CrewAI's task hierarchy and LiteLLM's model generation records in **one single trace**.

---

## 2. Frequently Asked Questions (Ticket #65 Deep Dive)

### Q1: Why does LiteLLM Proxy own the canonical model generation and cost records instead of CrewAI?
**Answer:**
1. **Financial Authority:** The enterprise LiteLLM Proxy connects directly to the model provider APIs, receives authoritative token usage from provider headers, and calculates exact USD costs based on enterprise model rate cards.
2. **Unified Ledger:** The proxy logs spend records directly into the central spend database. Having LiteLLM emit the canonical generation span ensures trace costs match financial invoices with **zero drift** (measured local variance was `$0.000000000004` or `0.000000167%` due solely to float rounding).
3. **Clean Separation of Concerns:** CrewAI focuses on agent orchestration logic; LiteLLM manages model routing, retries, rate limits, and billing.

### Q2: Why is no adapter needed for CrewAI Agent Delegation?
**Answer:**
Automatic instrumentation by OpenLIT already captures agent-to-agent delegation cleanly:
- When a manager agent delegates to a specialist, OpenLIT creates an `invoke_agent` child span representing the delegated specialist's execution.
- The parent agent, specialist agent, and handoff execution are already readable in the trace hierarchy with 87.5% baseline coverage. Adding an application-level wrapper introduces redundant spans without adding diagnostic value.

### Q3: Why is the Failure Adapter necessary for Retries?
**Answer:**
- When a tool fails and CrewAI retries, CrewAI catches the exception internally and invokes the tool again.
- While CrewAI detects the failure, raw automatic OpenTelemetry exporters do not retain low-cardinality metadata describing which tool failed, the number of retries attempted, or the ultimate fallback resolution.
- The `src/crewai_langfuse_demo/adapters/failure.py` adapter runs **only on failure/retry**, summarizing the retry cycle into a single safe `kolibri.crewai.failure_summary` span without logging sensitive stack traces.

### Q4: How does Composite Tool Observability work?
**Answer:**
- Standard CrewAI tools only emit a single `execute_tool` span for the parent function.
- If a tool performs complex internal sub-tasks (e.g., query database -> call payment API -> update cache), standard tracing hides those sub-operations.
- The `src/crewai_langfuse_demo/adapters/composite_tool.py` wrapper uses standard OpenTelemetry `start_as_current_span` with `gen_ai.operation.name = "execute_tool"` to expose these child operations as clean sub-spans in Langfuse.

### Q5: How is OpenTelemetry Context Propagated to LiteLLM Proxy?
**Answer:**
When CrewAI calls the LiteLLM Proxy via Python `requests` / `httpx`, OpenLIT automatically injects the active W3C `traceparent` header into the HTTP request headers. The LiteLLM Proxy extracts this `traceparent` header and attaches its generation span to the exact parent task span in Langfuse.

---

## 3. Known Limitations & Recommendations

1. **Named Delegated Policy Tasks:** While delegated agent execution is fully visible, CrewAI does not currently generate a distinct named task span for delegated policy evaluation. This is an upstream CrewAI design and does not impair diagnostic tracing.
2. **Local vs Enterprise Proxy:** Local testing uses `litellm-proxy/config.yaml`. In production, the service points to Konecta's managed LiteLLM cluster (`https://api.dev.ix.konecta-digital.com/litellm-test`), which handles authentication and rate limiting centrally.
