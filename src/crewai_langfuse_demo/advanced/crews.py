"""Three small advanced CrewAI workflows."""

from crewai import Agent, Crew, Process, Task

from ..config import Settings
from ..llm import create_llm
from .tools import lookup_exception_policy, lookup_retryable_order_status, resolve_order_exception


def build_retry_crew(settings: Settings) -> Crew:
    model = create_llm(settings)
    agent = Agent(
        role="Retry-aware order specialist",
        goal="Retry a temporary dependency failure until the safe tool succeeds.",
        backstory="For KOL-RETRY-123, retry the only available tool until it works.",
        tools=[lookup_retryable_order_status],
        llm=model,
        allow_delegation=False,
        max_iter=6,
        verbose=False,
    )
    task = Task(
        description="Find KOL-RETRY-123. The first two tool calls fail temporarily; retry until it succeeds.",
        expected_output="A one-sentence safe status after retry succeeds.",
        agent=agent,
    )
    return Crew(agents=[agent], tasks=[task], process=Process.sequential, tracing=False, verbose=False)


def build_delegation_crew(settings: Settings) -> Crew:
    model = create_llm(settings)
    specialist = Agent(
        role="Policy exception specialist",
        goal="Look up one safe policy recommendation.",
        backstory="You alone may use the policy lookup tool.",
        tools=[lookup_exception_policy],
        llm=model,
        allow_delegation=False,
        verbose=False,
    )
    coordinator = Agent(
        role="Customer support exception coordinator",
        goal="Delegate the policy decision and write a safe customer update.",
        backstory="You must delegate policy work to the specialist.",
        llm=model,
        allow_delegation=True,
        verbose=False,
    )
    task = Task(
        description="Delegate the carrier-delay policy decision to the specialist, then give a one-sentence safe update.",
        expected_output="A short safe customer update based on delegated policy advice.",
        agent=coordinator,
    )
    return Crew(
        agents=[coordinator, specialist],
        tasks=[task],
        process=Process.sequential,
        tracing=False,
        verbose=False,
    )


def build_composite_tool_crew(settings: Settings) -> Crew:
    model = create_llm(settings)
    agent = Agent(
        role="Order exception specialist",
        goal="Resolve the exception with the one parent tool.",
        backstory="Use only resolve_order_exception; do not invent data.",
        tools=[resolve_order_exception],
        llm=model,
        allow_delegation=False,
        verbose=False,
    )
    task = Task(
        description="Resolve KOL-COMPOSITE-456 with resolve_order_exception.",
        expected_output="A one-sentence safe combined result.",
        agent=agent,
    )
    return Crew(agents=[agent], tasks=[task], process=Process.sequential, tracing=False, verbose=False)

