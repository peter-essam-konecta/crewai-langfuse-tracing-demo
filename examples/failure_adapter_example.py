"""The smallest safe way to add the reusable failure adapter to one CrewAI run.

Full explanation:
https://github.com/peter-essam-konecta/crewai-langfuse-tracing-demo/blob/main/docs/failure-adapter-reference.md
"""

from __future__ import annotations

from typing import Any

from crewai import Crew

from crewai_langfuse_demo.adapters.failure import FailureAdapter


def run_crew_with_failure_summary(crew: Crew) -> Any:
    """Run one crew and add a safe summary only if one of its tools fails.

    This is the only integration needed for a CrewAI crew that requires
    readable failed-tool and retry information in Langfuse.
    """

    adapter = FailureAdapter()
    adapter.install()  # 1. Listen to CrewAI's existing tool events.
    try:
        result = crew.kickoff()  # 2. Run the crew normally.
        adapter.complete(crew_completed=bool(result))  # 3. Record safe final outcome.
        return result
    except BaseException:
        adapter.complete(crew_completed=False)  # 4. Record a safe aborted outcome.
        raise
    finally:
        adapter.uninstall()  # 5. Remove the temporary event listeners.


# Example use in your own runner:
#
# crew = build_your_crew()
# result = run_crew_with_failure_summary(crew)

