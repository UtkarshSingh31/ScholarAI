from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from app.graph import scholarship_graph


_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="scholarai")
_jobs: dict[str, dict[str, Any]] = {}
_lock = Lock()
_NODE_LABELS = {
    "profile_intelligence": "Profile Intelligence",
    "supervisor_profile": "Supervisor is deciding whether the profile is ready",
    "opportunity_hunter": "Opportunity Hunter",
    "supervisor_hunter": "Supervisor is evaluating search coverage",
    "evidence": "Evidence Extraction",
    "supervisor_evidence": "Supervisor is evaluating source coverage",
    "eligibility_auditor": "Eligibility and Evidence Auditor",
    "supervisor_auditor": "Supervisor is evaluating audit results",
    "matchmaker": "Matchmaker",
    "recommendation_reviewer": "Groq Recommendation Reviewer",
    "application_coach": "Application Coach",
}


def _next_node(node_name: str, state: dict[str, Any]) -> str:
    if node_name == "profile_intelligence":
        return "supervisor_profile"
    if node_name == "supervisor_profile":
        return (
            "opportunity_hunter"
            if state.get("supervisor_decision", {}).get("next_action")
            in {"continue", "retry_search"}
            else ""
        )
    if node_name == "opportunity_hunter":
        return "supervisor_hunter"
    if node_name == "supervisor_hunter":
        action = state.get("supervisor_decision", {}).get("next_action")
        return {
            "continue": "evidence",
            "retry_search": "opportunity_hunter",
        }.get(action, "")
    if node_name == "evidence":
        return "supervisor_evidence"
    if node_name == "supervisor_evidence":
        action = state.get("supervisor_decision", {}).get("next_action")
        return {
            "continue": "eligibility_auditor",
            "retry_evidence": "evidence",
            "retry_search": "opportunity_hunter",
        }.get(action, "")
    if node_name == "eligibility_auditor":
        return "supervisor_auditor"
    if node_name == "supervisor_auditor":
        action = state.get("supervisor_decision", {}).get("next_action")
        return {
            "continue": "matchmaker",
            "retry_evidence": "evidence",
            "retry_search": "opportunity_hunter",
        }.get(action, "")
    if node_name == "matchmaker":
        return "recommendation_reviewer"
    if node_name == "recommendation_reviewer":
        return "application_coach"
    return ""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_job(job_id: str, **updates: Any) -> None:
    with _lock:
        _jobs[job_id].update(updates, updated_at=_timestamp())


def _run_job(job_id: str, state: dict[str, Any]) -> None:
    try:
        _set_job(job_id, status="running")
        latest_state = dict(state)
        _set_job(
            job_id,
            current_node="profile_intelligence",
            activity="Running Profile Intelligence...",
        )

        for update in scholarship_graph.stream(
            state,
            {"run_name": f"ScholarAI workflow {job_id}"},
            stream_mode="updates",
        ):
            latest_state.update(next(iter(update.values()), {}))
            node_name = next(iter(update), "")
            statuses = dict(latest_state.get("agent_status", {}))
            if node_name:
                statuses[node_name] = "completed"
            next_node = _next_node(node_name, latest_state)
            if next_node:
                statuses[next_node] = "running"
            _set_job(
                job_id,
                agent_status=statuses,
                current_node=next_node,
                activity=(
                    f"Running {_NODE_LABELS.get(next_node, next_node)}..."
                    if next_node
                    else (
                        f"Completed {_NODE_LABELS.get(node_name, node_name)}."
                        if node_name
                        else "Workflow is processing..."
                    )
                ),
                profile_valid=latest_state.get("profile_valid", False),
                errors=list(latest_state.get("errors", [])),
            )

        _set_job(
            job_id,
            status="completed",
            result={
                "profile_valid": latest_state.get("profile_valid", False),
                "student_profile": latest_state.get("student_profile", {}),
                "profile_evidence": latest_state.get("profile_evidence", []),
                "eligibility_results": latest_state.get(
                    "eligibility_results",
                    [],
                ),
                "shortlist": latest_state.get("shortlist", []),
                "review": latest_state.get("review", {}),
                "application_draft": latest_state.get(
                    "application_draft",
                    "",
                ),
                "supervisor_decision": latest_state.get(
                    "supervisor_decision",
                    {},
                ),
                "agent_status": latest_state.get("agent_status", {}),
                "errors": latest_state.get("errors", []),
            },
            agent_status=latest_state.get("agent_status", {}),
            errors=latest_state.get("errors", []),
            current_node="",
            activity="Workflow completed.",
        )
    except Exception as exc:
        _set_job(
            job_id,
            status="failed",
            errors=[f"Workflow job failed: {type(exc).__name__}: {exc}"],
            current_node="",
            activity="Workflow failed.",
        )


def submit_job(state: dict[str, Any]) -> str:
    job_id = uuid4().hex
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "created_at": _timestamp(),
            "updated_at": _timestamp(),
            "agent_status": dict(state.get("agent_status", {})),
            "errors": [],
            "current_node": "",
            "activity": "Queued for processing.",
        }
    _executor.submit(_run_job, job_id, state)
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None
