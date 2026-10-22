
from langgraph.graph import StateGraph, START, END

from app.observability import LANGSMITH_ENABLED
from app.state import ScholarshipState
from app.nodes import (
    profile_intelligence_agent,
    opportunity_hunter_agent,
    evidence_node,
    eligibility_auditor_agent,
    matchmaker_agent,
    application_coach_agent,
)
from app.agents.reviewer import recommendation_reviewer_agent


def route_after_profile(state: ScholarshipState) -> str:
    """Continue only when the student profile is valid."""

    if state["profile_valid"]:
        return "opportunity_hunter"

    return "end"


def build_graph():
    builder = StateGraph(ScholarshipState)

    builder.add_node(
        "profile_intelligence",
        profile_intelligence_agent,
    )
    builder.add_node(
        "opportunity_hunter",
        opportunity_hunter_agent,
    )
    builder.add_node(
        "eligibility_auditor",
        eligibility_auditor_agent,
    )
    builder.add_node(
        "matchmaker",
        matchmaker_agent,
    )
    builder.add_node(
        "application_coach",
        application_coach_agent,
    )
    builder.add_node(
        "recommendation_reviewer",
        recommendation_reviewer_agent,
    )

    builder.add_edge(START, "profile_intelligence")

    builder.add_conditional_edges(
        "profile_intelligence",
        route_after_profile,
        {
            "opportunity_hunter": "opportunity_hunter",
            "end": END,
        },
    )

    builder.add_node("evidence", evidence_node)
    builder.add_edge("opportunity_hunter", "evidence")
    builder.add_edge("evidence", "eligibility_auditor")
    builder.add_edge("eligibility_auditor", "matchmaker")
    builder.add_edge("matchmaker", "recommendation_reviewer")
    builder.add_edge("recommendation_reviewer", "application_coach")
    builder.add_edge("application_coach", END)

    return builder.compile()


scholarship_graph = build_graph()
