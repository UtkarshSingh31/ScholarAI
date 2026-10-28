from typing import Any
import json

from schemas import RecommendationReview
from state import ScholarshipState
from config import GROQ_MODEL
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq


def recommendation_reviewer_agent(
    state: ScholarshipState,
) -> dict[str, Any]:
    """Independently review the evidence-supported recommendation shortlist."""

    shortlist = state.get("shortlist", [])
    if not shortlist:
        return {
            "review": {
                "status": "skipped",
                "reason": "No eligible recommendations were available.",
            },
            "agent_status": {
                **state.get("agent_status", {}),
                "recommendation_reviewer": "skipped",
            },
        }

    context = {
        "student_profile": state.get("student_profile", {}),
        "recommendations": shortlist,
        "instruction": (
            "Review the recommendations independently. Check whether each "
            "recommendation is supported by the supplied eligibility status, "
            "requirements, funding, deadline, and ranking reasons. Do not "
            "invent facts, perform new eligibility decisions, or upgrade "
            "unknown evidence to meets. List missing checks explicitly."
        ),
    }

    try:
        model = ChatGroq(
            model=GROQ_MODEL,
            temperature=0,
            max_retries=2,
        ).with_structured_output(
            RecommendationReview,
            method="function_calling",
        )
        review = model.invoke([
            SystemMessage(
                content=(
                    "You are an independent recommendation reviewer. "
                    "Return only the requested structured review."
                )
            ),
            HumanMessage(
                content=json.dumps(
                    context,
                    ensure_ascii=False,
                    default=str,
                )
            ),
        ])
    except Exception as exc:
        return {
            "review": {
                "status": "failed",
                "reason": (
                    f"Groq recommendation review failed: "
                    f"{type(exc).__name__}: {exc}"
                ),
            },
            "errors": state["errors"] + [
                f"Groq recommendation review failed: "
                f"{type(exc).__name__}: {exc}"
            ],
            "agent_status": {
                **state.get("agent_status", {}),
                "recommendation_reviewer": "failed",
            },
        }

    return {
        "review": {
            "status": "completed",
            **review.model_dump(),
        },
        "agent_status": {
            **state.get("agent_status", {}),
            "recommendation_reviewer": "completed",
        },
    }
