
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
from app.agents.supervisor import supervisor_agent


def _supervisor_route(
    state: ScholarshipState,
    allowed: set[str],
    default: str,
) -> str:
    action = state.get("supervisor_decision", {}).get("next_action")
    return action if action in allowed else default


def supervise_profile(state: ScholarshipState) -> dict:
    return supervisor_agent(state, "profile")


def supervise_hunter(state: ScholarshipState) -> dict:
    return supervisor_agent(state, "hunter")


def supervise_evidence(state: ScholarshipState) -> dict:
    return supervisor_agent(state, "evidence")


def supervise_auditor(state: ScholarshipState) -> dict:
    return supervisor_agent(state, "auditor")


def route_after_profile(state: ScholarshipState) -> str:
    if not state["profile_valid"]:
        return "end"
    action = state.get("supervisor_decision", {}).get("next_action")
    if action in {"continue", "retry_search"}:
        return "opportunity_hunter"
    return "end"


def route_after_hunter(state: ScholarshipState) -> str:
    return _supervisor_route(
        state,
        {"continue", "retry_search", "stop"},
        "evidence" if state.get("opportunities") else "end",
    )


def route_after_evidence(state: ScholarshipState) -> str:
    return _supervisor_route(
        state,
        {"continue", "retry_evidence", "retry_search", "stop"},
        "eligibility_auditor" if state.get("evidence") else "end",
    )


def route_after_auditor(state: ScholarshipState) -> str:
    return _supervisor_route(
        state,
        {"continue", "retry_evidence", "retry_search", "stop"},
        "matchmaker",
    )


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
    builder.add_node("supervisor_profile", supervise_profile)
    builder.add_node("supervisor_hunter", supervise_hunter)
    builder.add_node("supervisor_evidence", supervise_evidence)
    builder.add_node("supervisor_auditor", supervise_auditor)
    builder.add_node(
        "recommendation_reviewer",
        recommendation_reviewer_agent,
    )

    builder.add_edge(START, "profile_intelligence")

    builder.add_edge("profile_intelligence", "supervisor_profile")
    builder.add_conditional_edges(
        "supervisor_profile",
        route_after_profile,
        {"opportunity_hunter": "opportunity_hunter", "end": END},
    )

    builder.add_node("evidence", evidence_node)
    builder.add_edge("opportunity_hunter", "supervisor_hunter")
    builder.add_conditional_edges(
        "supervisor_hunter",
        route_after_hunter,
        {
            "continue": "evidence",
            "retry_search": "opportunity_hunter",
            "stop": END,
            "evidence": "evidence",
            "end": END,
        },
    )
    builder.add_edge("evidence", "supervisor_evidence")
    builder.add_conditional_edges(
        "supervisor_evidence",
        route_after_evidence,
        {
            "continue": "eligibility_auditor",
            "retry_evidence": "evidence",
            "retry_search": "opportunity_hunter",
            "stop": END,
            "eligibility_auditor": "eligibility_auditor",
            "end": END,
        },
    )
    builder.add_edge("eligibility_auditor", "supervisor_auditor")
    builder.add_conditional_edges(
        "supervisor_auditor",
        route_after_auditor,
        {
            "continue": "matchmaker",
            "retry_evidence": "evidence",
            "retry_search": "opportunity_hunter",
            "stop": END,
            "matchmaker": "matchmaker",
        },
    )
    builder.add_edge("matchmaker", "recommendation_reviewer")
    builder.add_edge("recommendation_reviewer", "application_coach")
    builder.add_edge("application_coach", END)

    return builder.compile()


scholarship_graph = build_graph()
