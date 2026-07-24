"""Run one basic or advanced example and show exactly when adapters are used."""

from __future__ import annotations

import argparse
import os

from .config import load_settings
from .tracing import configure_tracing, flush_tracing


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a CrewAI + Langfuse tracing example.")
    parser.add_argument("scenario", choices=("basic", "retry", "delegation", "composite-tool"))
    parser.add_argument("--failure-adapter", action="store_true")
    parser.add_argument("--composite-adapter", action="store_true")
    args = parser.parse_args()

    if args.failure_adapter and args.scenario != "retry":
        raise SystemExit("The failure adapter is only used in the retry example.")
    if args.composite_adapter and args.scenario != "composite-tool":
        raise SystemExit("The composite adapter is only used in the composite-tool example.")

    settings = load_settings()
    configure_tracing(settings)

    # Import CrewAI code only after tracing is configured.
    from .advanced.crews import build_composite_tool_crew, build_delegation_crew, build_retry_crew
    from .advanced.tools import configure_composite_adapter, reset_retry_state, retry_attempt_count
    from .basic.crew import build_crew

    if args.scenario == "basic":
        crew = build_crew(settings)
        explanation = "automatic tracing only"
    elif args.scenario == "retry":
        reset_retry_state()
        crew = build_retry_crew(settings)
        explanation = "automatic tracing plus the failure adapter" if args.failure_adapter else "automatic tracing only"
    elif args.scenario == "delegation":
        crew = build_delegation_crew(settings)
        explanation = "automatic tracing only"
    else:
        crew = build_composite_tool_crew(settings)
        explanation = "automatic tracing plus the composite-tool adapter" if args.composite_adapter else "automatic tracing only"

    failure_adapter = None
    composite_adapter_enabled = args.composite_adapter
    if args.failure_adapter:
        from .adapters.failure import FailureAdapter

        os.environ["DEMO_RETRY_TEST"] = "lookup_retryable_order_status"
        failure_adapter = FailureAdapter()
        failure_adapter.install()
    if composite_adapter_enabled:
        from .adapters.composite_tool import CompositeToolAdapter

        configure_composite_adapter(CompositeToolAdapter())

    print(f"Running {args.scenario} with {explanation}.")
    try:
        result = crew.kickoff()
        if failure_adapter:
            failure_adapter.complete(crew_completed=bool(result))
        print("\nFinal safe result:")
        print(result)
        if args.scenario == "retry":
            print(f"Safe local retry attempt count: {retry_attempt_count()}")
    except BaseException:
        if failure_adapter:
            failure_adapter.complete(crew_completed=False)
        raise
    finally:
        if failure_adapter:
            failure_adapter.uninstall()
            os.environ.pop("DEMO_RETRY_TEST", None)
        if composite_adapter_enabled:
            configure_composite_adapter(None)
        flush_tracing()
        print("\nTracing was flushed. Open Langfuse and inspect the newest trace.")


if __name__ == "__main__":
    main()

