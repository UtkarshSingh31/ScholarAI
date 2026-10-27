from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from app.graph import scholarship_graph


_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="scholarai")
_jobs: dict[str, dict[str, Any]] = {}
_lock = Lock()


def _event_details(
    node_name: str,
    update_state: dict[str, Any],
) -> list[str]:
    """Create concise, factual activity lines from the node's state update."""
    details: list[str] = []
    if node_name == "profile_intelligence":
        profile = update_state.get("student_profile", {})
        details.append(
            f"Profile established for {profile.get('name', 'student')}"
        )
        details.append(
            f"Countries: {', '.join(profile.get('preferred_countries', [])) or 'none'}"
        )
        details.append(
            f"Profile evidence items: {len(update_state.get('profile_evidence', []))}"
        )
    elif node_name == "opportunity_hunter":
        details.append(
            f"Collected {len(update_state.get('opportunities', []))} unique opportunities"
        )
        errors = update_state.get("errors", [])
        if errors:
            details.append(f"Warnings recorded: {len(errors)}")
    elif node_name == "evidence":
        metadata = update_state.get("extraction_metadata", {})
        details.append(
            f"Extracted evidence for {len(update_state.get('evidence', []))} source pages"
        )
        details.append(
            f"Processed {metadata.get('requested_url_count', 0)} URLs in "
            f"{metadata.get('batch_count', 0)} batch(es)"
        )
    elif node_name == "eligibility_auditor":
        results = update_state.get("eligibility_results", [])
        counts = {
            status: sum(item.get("status") == status for item in results)
            for status in ("meets", "does_not_meet", "unknown")
        }
        details.append(
            f"Audited {len(results)} opportunities: "
            f"{counts['meets']} pass, {counts['does_not_meet']} fail, "
            f"{counts['unknown']} unknown"
        )
    elif node_name == "matchmaker":
        details.append(
            f"Ranked {len(update_state.get('shortlist', []))} verified matches"
        )
    elif node_name.startswith("supervisor_"):
        decision = update_state.get("supervisor_decision", {})
        if decision:
            details.append(
                f"Supervisor action: {decision.get('next_action', 'unknown')}"
            )
            details.append(decision.get("reason", "No reason supplied."))
    elif node_name == "recommendation_reviewer":
        details.append("Recommendation review completed or was safely skipped.")
    elif node_name == "application_coach":
        details.append("Grounded application guidance was prepared.")
    return details


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
        events: list[dict[str, Any]] = []
        _set_job(
            job_id,
            current_node="profile_intelligence",
            events=events,
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
            event = {
                "timestamp": _timestamp(),
                "node": node_name,
                "status": "completed",
                "label": node_name.replace("_", " ").title(),
                "updated_fields": sorted(
                    next(iter(update.values()), {}).keys()
                ),
                "details": _event_details(
                    node_name,
                    next(iter(update.values()), {}),
                ),
                "counts": {
                    "opportunities": len(latest_state.get("opportunities", [])),
                    "evidence": len(latest_state.get("evidence", [])),
                    "eligibility": len(
                        latest_state.get("eligibility_results", [])
                    ),
                    "shortlist": len(latest_state.get("shortlist", [])),
                    "errors": len(latest_state.get("errors", [])),
                },
            }
            decision = latest_state.get("supervisor_decision", {})
            if node_name.startswith("supervisor_") and decision:
                event["decision"] = dict(decision)
            events.append(event)
            _set_job(
                job_id,
                agent_status=statuses,
                current_node=next_node,
                events=list(events),
                profile_valid=latest_state.get("profile_valid", False),
                student_profile=latest_state.get("student_profile", {}),
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
                "events": list(events),
                "agent_status": latest_state.get("agent_status", {}),
                "errors": latest_state.get("errors", []),
            },
            agent_status=latest_state.get("agent_status", {}),
            student_profile=latest_state.get("student_profile", {}),
            errors=latest_state.get("errors", []),
            current_node="",
            events=list(events),
        )
    except Exception as exc:
        _set_job(
            job_id,
            status="failed",
            errors=[f"Workflow job failed: {type(exc).__name__}: {exc}"],
            current_node="",
            events=locals().get("events", []),
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
            "events": [],
        }
    _executor.submit(_run_job, job_id, state)
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None
