# Implementation Handoff and Governance

> **Status:** Incubation Team R&D handoff for GitHub issue #65. This separates validated reference work from development implementation and approval.

## Ownership

| Role | Owner | Responsibility |
| :--- | :--- | :--- |
| Incubation R&D | Peter Essam | Safe POC, comparison evidence, reference adapters, documentation, and implementation support |
| Development implementation | Marwan Saad / Development Team | Target-service dependency review, integration, secrets, deployment, and development/staging validation |
| Technical approval | Lead Architect / Tech Lead | Service-specific exceptions, schema changes, and production readiness |
| Platform observability | Platform Observability Team | Langfuse/LiteLLM platform configuration and enterprise monitoring |

## Handoff package

This repository provides:

1. Four maintained scenarios: basic, retry/failure, delegation, and composite tool.
2. Two reusable, unit-tested R&D reference adapters.
3. A repository-specific mapping to the approved Final Trace Schema.
4. An exact integration guide and development acceptance checklist.
5. Evidence-backed architecture decisions with known limitations.
6. PowerShell helpers and Python `unittest` coverage.

It does not provide production credentials, target-service code, enterprise deployment approval, or complete enterprise cost/privacy evidence.

## Development sequence

1. Read `AGENTS.md` in its required order.
2. Run `.\scripts\setup.ps1` and `.\scripts\run-tests.ps1`.
3. Compare the target repository's dependency graph with the exact pins in `requirements.txt` before adding OpenLIT or OpenTelemetry packages.
4. Adapt `src/crewai_langfuse_demo/tracing.py` and `src/crewai_langfuse_demo/llm.py`; do not copy outdated prose snippets.
5. Add neither adapter by default. Enable one only for the matching measured gap.
6. Run the full checklist in `docs/developer-guide.md` in development/staging.
7. Record fresh trace IDs and cost/privacy evidence before requesting approval or closing issue #65.

If a required fact is not established by code, tests, or recorded evidence, mark it pending and ask the relevant owner instead of assuming it.

## Remaining development-owned validation after the R&D cleanup

Marwan / the Development Team still owns:

1. Resolving or accepting the target service's actual CrewAI/OpenLIT dependency behavior so normal tools export the Final Trace Schema fields rather than relying on the checker compatibility fallback.
2. Confirming that internal OpenLIT graph observations are mapped to valid operation types and carry every required attribute in the target dependency set.
3. Restoring and proving one connected trace with LiteLLM Proxy-owned canonical generations, tokens, latency, and cost in development/staging.
4. Capturing exporter- or collector-level evidence that canonical generations are `CLIENT` and normal tool executions are `INTERNAL`.
5. Completing target-environment privacy inspection, Proxy cost comparison, hierarchy review, deployment, and production-readiness evidence.

Peter / Incubation R&D retains ownership of this reference implementation, the corrected validation approach, evidence, acceptance criteria, and handoff support. These target-service actions do not move implementation ownership back to Peter.
