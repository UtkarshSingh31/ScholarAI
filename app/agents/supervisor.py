import json
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import GEMINI_MODEL
from schemas import SupervisorDecision
from state import ScholarshipState

SupervisorPhase = Literal["profile", "hunter", "evidence", "auditor"]
MAX_RETRIES_PER_PHASE = 2
MAX_SUPERVISOR_STEPS = 8


def supervisor_agent(
    state: ScholarshipState,
    phase: SupervisorPhase,
) -> dict[str, Any]:
    """Choose the next bounded workflow action from the current state."""

    opportunities = state.get("opportunities", [])
    evidence = state.get("evidence", [])
    eligibility = state.get("eligibility_results", [])
    retry_counts = dict(state.get("supervisor_retry_counts", {}))
    previous_decision = state.get("supervisor_decision", {})
    retries = retry_counts.get(phase, 0)
    if (
        phase not in retry_counts
        and previous_decision.get("phase") == phase
    ):
        retries = state.get("supervisor_retries", 0)
    steps = state.get("supervisor_steps", 0)
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

    allowed_actions = {
        "profile": {"continue", "stop"},
        "hunter": {"continue", "retry_search", "stop"},
        "evidence": {
            "continue",
            "retry_evidence",
            "retry_search",
            "stop",
        },
        "auditor": {
            "continue",
            "retry_evidence",
            "retry_search",
            "stop",
        },
    }[phase]

    if decision is not None and decision.next_action not in allowed_actions:
        error = (
            f"Supervisor returned invalid action {decision.next_action!r} "
            f"for phase {phase}."
        )
        decision = None

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
    steps += 1
    if steps > MAX_SUPERVISOR_STEPS:
        action = "stop"
        decision_data = {
            "next_action": action,
            "reason": (
                "Supervisor step limit reached; stopping to prevent "
                "workflow looping."
            ),
        }

    if action in {"retry_search", "retry_evidence"}:
        if retries >= MAX_RETRIES_PER_PHASE:
            decision_data = {
                "next_action": "stop",
                "reason": (
                    f"Supervisor retry limit reached for {phase}; "
                    "preserving the available evidence."
                ),
            }
        else:
            retries += 1
            retry_counts[phase] = retries

    errors = list(state.get("errors", []))
    if error:
        errors.append(error)

    return {
        "supervisor_retries": retries,
        "supervisor_retry_counts": retry_counts,
        "supervisor_steps": steps,
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
