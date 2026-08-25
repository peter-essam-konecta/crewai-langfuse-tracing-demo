# Trace Schema Contract: OpenTelemetry Spine for GenAI Channels

> **Status:** Approved cross-channel standard (Issue #63). Canonical reference for all Kolibri GenAI channels routing into Langfuse.

## 1. Overview and Core Principles

This document defines the unified OpenTelemetry (OTel) trace schema for GenAI agent channels routing into Langfuse. It adheres strictly to the official [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) for all standardized concepts, and uses the `kolibri.*` prefix for platform-specific fields.

### Three Global Invariants
1. **No custom keys inside `gen_ai.*`:** Never invent non-standard keys in the reserved `gen_ai.*` namespace. All enterprise extensions belong in `kolibri.*`.
2. **Provider Name Accuracy:** `gen_ai.provider.name` is always the real model vendor (e.g., `openai`, `gcp.gemini`, `groq`). LiteLLM is the transport proxy, not the provider. The execution engine is captured in `kolibri.runtime.name`.
3. **No Double-Counting:** LiteLLM Proxy HTTP transport records (e.g., `POST /chat/completions`) and canonical generation spans in the same trace belong to the same request. Dashboards and cost checks count only the generation span.

---

## 2. Root-Span / Workflow Attributes (The Agent Run)

Every agent or crew execution creates exactly one canonical workflow run span.

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `gen_ai.operation.name` | `string` | The execution type (`invoke_agent` for single agent, `invoke_workflow` for crew). | `"invoke_workflow"` |
| `gen_ai.agent.id` | `string` | Unique identifier of the crew or agent definition. | `"customer-support-crew"` |
| `kolibri.tenant.id` | `string` | Internal workspace / tenant identifier. | `"konecta-customer-service"` |
| `kolibri.channel` | `string` | Interaction modality (`"chat"`, `"voice"`, `"messaging"`). | `"chat"` |
| `kolibri.runtime.name` | `string` | Execution framework (`"crewai"`, `"elevenlabs"`, `"google_adk"`). | `"crewai"` |
| `gen_ai.conversation.id` | `string` | Pseudonymous session key linking turns across conversations. | `"conv-session-9988"` |
| `gen_ai.usage.cost` | `double` | Calculated total financial cost in USD (Langfuse convention). | `0.002396` |

---

## 3. Child-Span Types (CrewAI Operations)

All child spans define their execution type using standard `gen_ai.operation.name`.

### A. Agent Step (Sub-Agent Execution)
- **`gen_ai.operation.name`**: `"invoke_agent"`
- **Span Name**: `invoke_agent {agent.name}`
- **Required Attributes**:
  - `gen_ai.agent.name`: Descriptive name of the specialist agent (e.g., `"Order Verification Specialist"`).

### B. LLM Generation (Model Call)
- **Span Kind**: `CLIENT`
- **`gen_ai.operation.name`**: `"chat"` (or `"generate_content"`)
- **Required Attributes** (Emitted canonically by LiteLLM Proxy):
  - `gen_ai.provider.name`: Actual vendor (`"openai"`, `"gcp.gemini"`, `"groq"`).
  - `gen_ai.request.model`: Requested model alias or identifier.
  - `gen_ai.response.model`: Model returned in the API response.
  - `gen_ai.usage.input_tokens`: Prompt token count.
  - `gen_ai.usage.output_tokens`: Completion token count.
  - `gen_ai.usage.cost`: Total cost of the generation in USD.
  - `gen_ai.response.finish_reasons`: Array of finish reasons (e.g., `["stop"]`).

### C. Tool Execution
- **Span Kind**: `INTERNAL`
- **`gen_ai.operation.name`**: `"execute_tool"`
- **Span Name**: `execute_tool {tool.name}`
- **Required Attributes**:
  - `gen_ai.tool.name`: Name of the executed tool (e.g., `"lookup_order_status"`).
  - `kolibri.system`: Target backend system (e.g., `"crm_database"`).

---

## 4. Reusable Failure & Composite Extension Attributes

When standard automatic tracing has visibility gaps during advanced scenarios, the approved safe adapters emit standard `kolibri.*` extension attributes:

### A. Failure Summary (`kolibri.crewai.failure_summary`)
Emitted by `src/crewai_langfuse_demo/adapters/failure.py` when tool retries or failures occur:
- `kolibri.failed_tool.name`: Name of the failing tool (e.g., `"lookup_order_status"`).
- `kolibri.error.type`: Low-cardinality error classifier (e.g., `"controlled_test_failure"`, `"timeout"`).
- `kolibri.retry.count`: Number of retry attempts made before failure/recovery.
- `kolibri.recovery.outcome`: Final status (`"fallback_completed"`, `"recovered"`, `"unhandled_exception"`).

### B. Composite Child Operations (`execute_tool {child_op}`)
Emitted by `src/crewai_langfuse_demo/adapters/composite_tool.py` for operations nested inside a parent tool:
- `gen_ai.operation.name`: `"execute_tool"`
- `gen_ai.tool.name`: Child operation name (e.g., `"fetch_crm_history"`).
- `kolibri.composite.parent_tool`: Name of enclosing tool (`"resolve_order_exception"`).
- `kolibri.composite.is_child_operation`: `true`.
- `kolibri.system`: Backend service being called (`"crm_service"`).

---

## 5. Privacy, PII, and Payload By Reference

To comply with data protection regulations and ensure zero-PII in telemetry:
1. **Raw Content Prohibited:** Customer names, emails, phone numbers, raw prompt texts, completions, tool input arguments, tool output JSONs, and raw exception stack traces must **NEVER** be stored in span attributes.
2. **Payload References (When Content Store is Active):**
   - `kolibri.content.ref`: URI of the sanitized payload in the governed content store (e.g., `gs://kolibri-telem/session_9988/tool-io.json`).
   - `kolibri.content.sha256`: SHA-256 integrity hash of the referenced payload.
3. **OpenLIT Setting:** `capture_message_content=False` is strictly enforced.
