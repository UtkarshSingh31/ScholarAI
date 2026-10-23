from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from app.graph import scholarship_graph


_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="scholarai")
_jobs: dict[str, dict[str, Any]] = {}
_lock = Lock()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_job(job_id: str, **updates: Any) -> None:
    with _lock:
        _jobs[job_id].update(updates, updated_at=_timestamp())


def _run_job(job_id: str, state: dict[str, Any]) -> None:
    try:
        _set_job(job_id, status="running")
        latest_state = dict(state)

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
            _set_job(
                job_id,
                agent_status=statuses,
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
        )
    except Exception as exc:
        _set_job(
            job_id,
            status="failed",
            errors=[f"Workflow job failed: {type(exc).__name__}: {exc}"],
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
        }
    _executor.submit(_run_job, job_id, state)
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None
