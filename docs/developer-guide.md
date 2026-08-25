# CrewAI Traceability Pattern: Developer Integration Guide

> **Status:** Reference integration guide and acceptance checklist for developers and AI coding agents instrumenting CrewAI services for Langfuse.

---

## 1. Purpose

This guide outlines the standard recipe to instrument any CrewAI service at Konecta with LiteLLM Proxy and Langfuse, using the **Automatic-First** pattern.

By following this guide, you ensure:
- Complete visibility of crews, agents, tasks, tools, and model calls in **one connected Langfuse trace**.
- Accurate financial cost calculation matching LiteLLM Proxy ledgers.
- Full compliance with the approved **Final Trace Schema**.
- Strict privacy protection with zero prompt or PII leakage.

---

## 2. Architecture & Data Flow

```text
CrewAI Application Process
  │  (Automatic agent, task, and tool execution spans)
  ▼
OpenLIT (with schema & privacy filters)
  │  (Propagates OpenTelemetry traceparent context via HTTP headers)
  ▼
Langfuse Cloud / Self-Hosted ◄────────── LiteLLM Enterprise Proxy
                                            │
                                            │ (Canonical LLM generation spans,
                                            │  token counts, latency, and USD cost)
                                            ▼
                                     Model Provider (e.g. Gemini / Groq / OpenAI)
```

---

## 3. Step-by-Step Integration Recipe (6 Steps)

### Step 1: Add Dependencies
Ensure your project's `requirements.txt` or `pyproject.toml` includes:
```text
crewai>=0.100.0
openlit>=1.35.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-exporter-otlp>=1.20.0
```

### Step 2: Configure Environment Variables
Set the following environment variables through your service's secure configuration manager (never commit `.env`):
```bash
# Langfuse OTLP Tracing
LANGFUSE_BASE_URL="https://cloud.langfuse.com"
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."

# LiteLLM Proxy
LITELLM_PROXY_HOST="https://api.dev.ix.konecta-digital.com/litellm-test"
LITELLM_MASTER_KEY="sk-..."
LITELLM_MODEL="openai/gemini-2.5-flash-nothink"

# Platform Metadata
OTEL_SERVICE_NAME="customer-support-crewai"
DEPLOYMENT_ENVIRONMENT="development"
KOLIBRI_TENANT_ID="konecta-customer-service"
KOLIBRI_CHANNEL="chat"
```

### Step 3: Initialize OpenLIT Tracing at Startup
Create or import `init_tracing()` and invoke it at the **very top of your application entrypoint before importing CrewAI**:

```python
import os
import openlit
from opentelemetry import trace

def init_tracing():
    """Initializes OpenLIT with Langfuse exporter and privacy controls."""
    langfuse_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    
    # Configure OpenLIT once
    openlit.init(
        environment=os.getenv("DEPLOYMENT_ENVIRONMENT", "development"),
        application_name=os.getenv("OTEL_SERVICE_NAME", "crewai-service"),
        otlp_endpoint=f"{langfuse_url}/api/public/otel/v1/traces",
        otlp_headers={"Authorization": f"Basic {public_key}:{secret_key}"},
        capture_message_content=False,   # Strictly disable message text capture
        disable_batch=False
    )
```

### Step 4: Configure CrewAI LLM Client to Route Through LiteLLM Proxy
In your crew configuration or agent setup, use CrewAI's `LLM` class pointing to the proxy:

```python
import os
from crewai import LLM

def get_llm():
    return LLM(
        model=os.getenv("LITELLM_MODEL", "openai/gemini-2.5-flash-nothink"),
        base_url=f"{os.getenv('LITELLM_PROXY_HOST')}/v1",
        api_key=os.getenv("LITELLM_MASTER_KEY")
    )
```

### Step 5: (Optional) Attach Failure Adapter for Retries
If your crew uses tools that may fail and retry:
```python
from crewai_langfuse_demo.adapters.failure import observe_crew_failures

with observe_crew_failures(crew, workflow_name="Customer Order Resolution"):
    result = crew.kickoff(inputs={"order_id": "ORD-123"})
```

### Step 6: (Optional) Wrap Child Operations in Composite Tools
If a tool executes multiple distinct backend sub-operations:
```python
from crewai_langfuse_demo.adapters.composite_tool import observe_child_operation

@tool("sync_account")
def sync_account(account_id: str):
    with observe_child_operation("sync_account", "validate_billing", system="billing_db"):
        # sub-operation 1
        pass
        
    with observe_child_operation("sync_account", "update_crm", system="crm_service"):
        # sub-operation 2
        pass
```

---

## 4. Development Acceptance Checklist (11 Points)

Before marking a CrewAI service as production-ready, verify that its traces satisfy all 11 criteria:

- [ ] **1. Single Connected Trace:** The entire crew run (crew, agents, tasks, tools, and LiteLLM model calls) appears in exactly one Langfuse trace.
- [ ] **2. Correct Hierarchy:** Spans nest cleanly: `Workflow -> Agent Step -> Task -> Tool -> Model Generation`.
- [ ] **3. Canonical LLM Generation:** Model calls appear as canonical Langfuse Generation objects, not generic spans.
- [ ] **4. Accurate Cost & Tokens:** `gen_ai.usage.cost` (or `litellm.cost.total`), `prompt_tokens`, and `completion_tokens` match the LiteLLM Proxy response.
- [ ] **5. No Transport Duplication:** LiteLLM HTTP transport records (`POST /chat/completions`) are not counted as extra model calls.
- [ ] **6. Mandatory Metadata:** Root span includes `kolibri.tenant.id`, `gen_ai.conversation.id`, `gen_ai.agent.id`, `kolibri.runtime.name = "crewai"`, and `kolibri.channel`.
- [ ] **7. Content Privacy:** `capture_message_content` is `False`. No prompts, completions, customer names, or PII appear in span attributes.
- [ ] **8. Safe Error Handling:** Failed tool executions log low-cardinality `error.type` and standard OTel status `ERROR` without raw stack traces.
- [ ] **9. Failure Summary on Retry:** When a retry occurs, `kolibri.crewai.failure_summary` records failed tool, retry count, and outcome.
- [ ] **10. Composite Tool Observability:** Internal child operations inside complex tools appear as standard `execute_tool` spans with `kolibri.composite.*` markers.
- [ ] **11. Unit & Regression Tests:** All project unit tests pass cleanly with zero regression.
