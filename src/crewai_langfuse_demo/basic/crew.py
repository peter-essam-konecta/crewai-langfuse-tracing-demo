"""A simple three-agent CrewAI support workflow."""

from crewai import Agent, Crew, Process, Task

from ..config import Settings
from ..llm import create_llm
from .tools import create_response_checklist, get_refund_policy, lookup_order_status


def build_crew(settings: Settings) -> Crew:
    """Build the basic use case. It needs no custom adapter."""

    model = create_llm(settings)
    order_agent = Agent(
        role="Order status specialist",
        goal="Find the safe order status using the local tool.",
        backstory="You use only the order-status tool and never invent facts.",
        tools=[lookup_order_status],
        llm=model,
        allow_delegation=False,
        verbose=False,
    )
    policy_agent = Agent(
        role="Refund policy specialist",
        goal="Find the relevant safe policy.",
        backstory="You use only the policy tool.",
        tools=[get_refund_policy],
        llm=model,
        allow_delegation=False,
        verbose=False,
    )
    response_agent = Agent(
        role="Customer response specialist",
        goal="Create a short, calm, customer-support response plan.",
        backstory="You combine verified facts into a helpful next step.",
        tools=[create_response_checklist],
        llm=model,
        allow_delegation=False,
        verbose=False,
    )
    order_task = Task(
        description="Find the status for safe demo order KOL-123.",
        expected_output="One short order-status finding.",
        agent=order_agent,
    )
    policy_task = Task(
        description="Find the policy for delayed order KOL-123 in Egypt.",
        expected_output="One short policy finding.",
        agent=policy_agent,
    )
    response_task = Task(
        description="Use the response checklist and combine the earlier findings into one short support plan.",
        expected_output="A concise customer-support response plan.",
        agent=response_agent,
        context=[order_task, policy_task],
    )
    return Crew(
        agents=[order_agent, policy_agent, response_agent],
        tasks=[order_task, policy_task, response_task],
        process=Process.sequential,
        tracing=False,
        verbose=False,
    )

