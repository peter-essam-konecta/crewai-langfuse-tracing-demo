# AI Agent Instructions & Single Source of Truth

Welcome to the **CrewAI + Langfuse Observability Reference Repository**.

This repository is the canonical Single Source of Truth (SSOT) for instrumenting CrewAI multi-agent systems with LiteLLM Proxy and Langfuse at Konecta. Whether you are an AI coding assistant (Cursor, Claude Code, Antigravity, GitHub Copilot, Windsurf) or a human engineer, follow this document to navigate, understand, and modify the codebase without making unverified assumptions.

---

## 1. Required Reading Order

Before proposing, generating, or modifying any code or configuration, read the documentation in this strict order:

1. **`AGENTS.md` (This File):** Ground rules, architectural invariants, and anti-patterns.
2. **`docs/trace-schema-contract.md`:** The approved cross-channel trace schema (Issue #63 / Final Trace Schema).
3. **`docs/developer-guide.md`:** The production integration guide and 11-point development acceptance checklist.
4. **`docs/architecture-decisions-and-faq.md`:** Architectural Decision Records (ADRs), tool comparison benchmarks, and answers to Ticket #65 questions.
5. **`docs/implementation-handoff.md`:** Role boundaries between Incubation R&D (Peter) and Development Implementation (Marwan).
6. **`docs/trace-verification-and-evidence.md`:** Live Langfuse Cloud trace IDs, expected observation counts, and span hierarchy trees.
7. **`README.md`:** Quickstart and PowerShell script navigation.

---

## 2. Core Architectural Invariants (Non-Negotiable)

Any AI agent generating code in this repository or adapting this pattern for other services **MUST** adhere strictly to the following rules:

### A. The "Automatic-First" Principle
- **Do NOT invent manual spans** around standard CrewAI workflows, agents, tasks, or normal tools.
- OpenLIT instruments CrewAI framework operations automatically. Adding manual application spans leads to duplicated, conflicting observations in Langfuse.
- Only two explicit, narrowly-scoped adapters are permitted:
  1. **Failure Adapter (`src/crewai_langfuse_demo/adapters/failure.py`):** Adds a single `kolibri.crewai.failure_summary` span **only** when a tool execution fails and triggers retries or fallbacks.
  2. **Composite Tool Adapter (`src/crewai_langfuse_demo/adapters/composite_tool.py`):** Wraps internal child operations hidden inside a complex parent tool using standard `execute_tool` child spans.
- **Delegation requires NO custom adapter:** Standard agent-to-agent delegation is captured automatically by OpenLIT.

### B. Single Responsibility for Model Generation & Cost
- **CrewAI / OpenLIT owns workflow telemetry:** Crews, agents, tasks, and tool execution spans.
- **LiteLLM Proxy owns canonical LLM generations:** Token counts, prompt/completion token usage, latency, and financial cost (`gen_ai.usage.cost` / `litellm.cost.total`).
- **Never double-count:** HTTP transport records (e.g., `POST /chat/completions`) and model generation spans in the same trace belong to the same request. Telemetry dashboards count the canonical generation span.
- **Context Propagation:** The application runtime must propagate the OpenTelemetry `traceparent` context header across HTTP requests to the LiteLLM Proxy so that LLM calls appear inside the exact parent task span.

### C. Strict Schema Adherence
- All trace attributes must comply with the approved **Final Trace Schema (`docs/trace-schema-contract.md`)**.
- **Mandatory Root Attributes:**
  - `kolibri.tenant.id` (e.g., `"konecta-customer-service"`)
  - `gen_ai.conversation.id` (Session identifier)
  - `gen_ai.agent.id` (e.g., `"order-support-crew"`)
  - `kolibri.runtime.name` (Value: `"crewai"`)
  - `kolibri.channel` (Value: `"chat"`, `"voice"`, or `"messaging"`)
- **Prohibited:** Never invent custom keys inside the official `gen_ai.*` namespace. Use `kolibri.*` for custom enterprise extensions.

### D. Zero-PII and Content Privacy
- **Prompts, raw completions, tool arguments, tool outputs, and raw stack traces must NEVER be captured** in telemetry or stored in source files.
- OpenLIT privacy controls (`capture_message_content=False`) are enabled by default in `src/crewai_langfuse_demo/tracing.py`.
- Low-cardinality error identifiers (e.g., `error.type = "controlled_test_failure"`) are recorded instead of raw customer exception strings.

### E. Single Instrumentation Exporter Rule
- Use **OpenLIT** as the sole automatic instrumentation library.
- **Never enable OpenInference, OpenLLMetry, or CrewAI's proprietary hosted tracing** in the same process as OpenLIT, as this causes duplicate and fragmented traces.

---

## 3. Codebase Layout & Key Files

```text
crewai-langfuse-tracing-demo/
|-- AGENTS.md                                # Master AI instructions & SSOT (This file)
|-- README.md                                # Developer onboarding & navigation
|-- requirements.txt                         # Application Python dependencies
|-- requirements-proxy.txt                   # Local proxy dependencies (optional)
|
|-- src/crewai_langfuse_demo/
|   |-- __init__.py
|   |-- config.py                            # Safe environment settings & defaults
|   |-- llm.py                               # LiteLLM Proxy LLM client factory
|   |-- main.py                              # Entry point for running scenarios
|   |-- tracing.py                           # OpenLIT initialization & trace bootstrap
|   |
|   |-- adapters/
|   |   |-- __init__.py
|   |   |-- failure.py                       # Error-only failure summary adapter
|   |   `-- composite_tool.py                # Safe child-operation adapter
|   |
|   |-- basic/
|   |   |-- __init__.py
|   |   |-- crew.py                          # 3-agent baseline order support crew
|   |   `-- tools.py                         # Baseline fictional customer support tools
|   |
|   `-- advanced/
|       |-- __init__.py
|       |-- crews.py                         # Retry, Delegation, and Composite crews
|       `-- tools.py                         # Advanced tools (retry-trigger, composite)
|
|-- docs/
|   |-- trace-schema-contract.md             # Authoritative schema specification
|   |-- developer-guide.md                   # 6-step integration guide & checklist
|   |-- architecture-decisions-and-faq.md    # ADRs, tool comparison & Ticket #65 Q&A
|   |-- implementation-handoff.md            # Role boundaries (Incubation vs Dev)
|   |-- trace-verification-and-evidence.md   # Live Langfuse trace IDs & trees
|   |-- failure-adapter-reference.md         # Detailed failure adapter docs
|   |-- composite-tool-adapter-reference.md  # Detailed composite adapter docs
|   |-- how-tracing-works.md                 # Tracing mechanics
|   |-- how-adapters-work.md                 # Adapter mechanics
|   |-- scripts-reference.md                 # PowerShell scripts reference
|   `-- troubleshooting.md                   # Troubleshooting guide
|
|-- examples/
|   |-- failure_adapter_example.py           # Minimal failure adapter script
|   `-- composite_tool_adapter_example.py    # Minimal composite adapter script
|
|-- litellm-proxy/                           # Local LiteLLM Proxy configs & test routes
|-- scripts/                                 # PowerShell automation scripts
`-- tests/                                   # Unit tests for tools and adapters
```

---

## 4. Common Agent Workflows & Implementation Recipes

### Recipe 1: Initializing Tracing in a CrewAI Application
Always call `init_tracing()` **before** importing any CrewAI classes:

```python
from crewai_langfuse_demo.tracing import init_tracing

# 1. Initialize tracing FIRST
init_tracing(
    service_name="customer-support-crewai",
    environment="development",
    tenant_id="konecta-customer-service",
    conversation_id="conv-session-1234",
    agent_id="order-support-crew",
    channel="chat"
)

# 2. Import and build CrewAI objects AFTER tracing initialization
from crewai import Agent, Crew, Process, Task
```

### Recipe 2: Wrapping a Crew with the Failure Adapter
Use the failure adapter only when observing crews that perform retries or fallbacks:

```python
from crewai_langfuse_demo.adapters.failure import observe_crew_failures

# Attach the adapter around kickoff
with observe_crew_failures(crew, workflow_name="Order Support Retry Workflow"):
    result = crew.kickoff(inputs={"order_id": "ORD-999"})
```

### Recipe 3: Instrumenting Internal Child Operations of a Composite Tool
When a single parent tool performs multiple independent backend operations (e.g., querying CRM then validating inventory):

```python
from crewai_langfuse_demo.adapters.composite_tool import observe_child_operation

@tool("resolve_order_exception")
def resolve_order_exception(order_id: str) -> str:
    """Composite tool that executes multiple child operations."""
    
    # Child operation 1
    with observe_child_operation(
        parent_tool_name="resolve_order_exception",
        child_operation_name="fetch_crm_history",
        system="crm_service"
    ):
        history = crm_client.get(order_id)
        
    # Child operation 2
    with observe_child_operation(
        parent_tool_name="resolve_order_exception",
        child_operation_name="verify_warehouse_stock",
        system="inventory_service"
    ):
        stock = inventory_client.check(order_id)
        
    return "Resolution complete"
```

---

## 5. Validation and Testing Commands

When verifying code changes locally, execute the following commands from the repository root:

```powershell
# 1. Run local unit tests (No external network calls needed)
pytest -v

# OR using the PowerShell test wrapper:
.\scripts\run-tests.ps1

# 2. Run scenarios against Langfuse & LiteLLM Proxy (requires configured .env)
.\scripts\run-basic.ps1
.\scripts\run-retry.ps1
.\scripts\run-delegation.ps1
.\scripts\run-composite-tool.ps1

# 3. Inspect a specific trace in Langfuse
.\scripts\check-trace.ps1 -TraceId <TRACE_ID>
```

---

## 6. Prohibited Anti-Patterns Summary

| Prohibited Action | Why It Is Forbidden | Correct Alternative |
| :--- | :--- | :--- |
| Adding manual `tracer.start_span("run_agent")` | Causes duplicate, conflicting spans in Langfuse. | Rely on OpenLIT automatic instrumentation. |
| Hardcoding API keys or endpoints in code | Security vulnerability. | Load from environment variables via `src/crewai_langfuse_demo/config.py`. |
| Logging customer prompts or tool payloads | Violates data privacy and compliance policies. | Capture low-cardinality metadata and references only. |
| Importing CrewAI before `init_tracing()` | OpenLIT hooks will fail to wrap CrewAI classes properly. | Always invoke `init_tracing()` at the very top of the process entrypoint. |
| Inventing custom `gen_ai.*` attributes | Violates the official OpenTelemetry GenAI Semantic Conventions. | Use the `kolibri.*` namespace for custom fields. |
