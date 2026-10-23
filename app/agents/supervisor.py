import json
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GEMINI_MODEL
from app.schemas import SupervisorDecision
from app.state import ScholarshipState

SupervisorPhase = Literal["profile", "hunter", "evidence", "auditor"]


def supervisor_agent(
    state: ScholarshipState,
    phase: SupervisorPhase,
) -> dict[str, Any]:
    """Choose the next bounded workflow action from the current state."""

    opportunities = state.get("opportunities", [])
    evidence = state.get("evidence", [])
    eligibility = state.get("eligibility_results", [])
    retries = state.get("supervisor_retries", 0)
    previous_phase = state.get(
        "supervisor_decision",
        {},
    ).get("phase")
    if previous_phase != phase:
        retries = 0
    summary = {
        "phase": phase,
        "profile_valid": state.get("profile_valid", False),
        "opportunity_count": len(opportunities),
        "evidence_count": len(evidence),
        "eligibility_counts": {
            status: sum(
                item.get("status") == status
                for item in eligibility
            )
            for status in ("meets", "does_not_meet", "unknown")
        },
        "retry_count": retries,
        "recent_errors": state.get("errors", [])[-5:],
        "instruction": (
            "Choose the next action for this workflow phase. Continue when "
            "the current output is sufficient. Retry search when candidates "
            "are missing or weak. Retry evidence when source coverage is "
            "missing. At the profile phase, choose only continue or stop. "
            "At the hunter phase, choose continue, retry_search, or stop. "
            "At the evidence and auditor phases, choose continue, "
            "retry_evidence, retry_search, or stop. Stop when continuing "
            "would not improve the result. "
            "Never stop a valid path merely because some individual source "
            "failed. Do not decide eligibility yourself."
        ),
    }

    decision: SupervisorDecision | None = None
    error: str | None = None
    try:
        model = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=0,
            max_retries=2,
        ).with_structured_output(
            SupervisorDecision,
            method="json_schema",
        )
        decision = model.invoke([
            SystemMessage(
                content=(
                    "You are the ScholarAI workflow supervisor. Route work "
                    "between specialized agents using only the supplied "
                    "workflow summary. Return one structured decision."
                )
            ),
            HumanMessage(content=json.dumps(summary, ensure_ascii=False)),
        ])
    except Exception as exc:
        error = (
            f"Supervisor decision failed: {type(exc).__name__}: {exc}"
        )

    if decision is None:
        if phase == "profile":
            action = "continue" if state.get("profile_valid") else "stop"
        elif phase == "hunter":
            action = "continue" if opportunities else "retry_search"
        elif phase == "evidence":
            action = "continue" if evidence else "retry_evidence"
        else:
            action = "continue" if any(
                item.get("status") == "meets" for item in eligibility
            ) else "stop"
        decision_data = {
            "next_action": action,
            "reason": error or "Used the safe supervisor fallback.",
        }
    else:
        decision_data = decision.model_dump()

    action = decision_data["next_action"]
    if action in {"retry_search", "retry_evidence"}:
        if retries >= 2:
            decision_data = {
                "next_action": "stop",
                "reason": (
                    "Supervisor retry limit reached; preserving the "
                    "available evidence."
                ),
            }
        else:
            retries += 1

    errors = list(state.get("errors", []))
    if error:
        errors.append(error)

    return {
        "supervisor_retries": retries,
        "supervisor_decision": {
            "phase": phase,
            **decision_data,
        },
        "errors": errors,
        "agent_status": {
            **state.get("agent_status", {}),
            "supervisor": "completed" if decision else "fallback",
        },
    }
