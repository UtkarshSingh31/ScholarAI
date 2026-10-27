import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from app.graph import scholarship_graph
from app.jobs import get_job, submit_job
from app.observability import LANGSMITH_ENABLED


app = FastAPI(
    title="ScholarAI",
    description="Evidence-backed scholarship discovery workflow.",
    version="0.1.0",
)
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
STATIC_DIR = (
    FRONTEND_DIST
    if (FRONTEND_DIST / "index.html").exists()
    else Path(__file__).parent / "static"
)
REQUIRED_PROFILE_FIELDS = {
    "name": "full name",
    "nationality": "nationality/citizenship",
    "degree": "current degree",
    "current_degree_level": "current degree level",
    "graduation_status": "graduation status",
    "target_degree_level": "target degree level",
    "target_field": "target field",
    "target_intake": "target intake/year",
    "budget": "funding need",
}


def _validate_profile_inputs(profile: dict[str, Any]) -> None:
    missing = [
        label for key, label in REQUIRED_PROFILE_FIELDS.items()
        if profile.get(key) is None
        or (isinstance(profile.get(key), str) and not profile[key].strip())
    ]
    countries = profile.get("preferred_countries")
    if not isinstance(countries, list) or not countries:
        missing.append("at least one destination country")
    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Complete the required profile fields before "
                "starting scholarship research.",
                "missing_fields": missing,
            },
        )


def _parse_json_object(value: str, field_name: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must contain valid JSON.",
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a JSON object.",
        )
    return parsed


def _parse_url_list(value: str) -> list[str]:
    if not value.strip():
        return []

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="profile_urls must contain a JSON array of strings.",
        ) from exc

    if (
        not isinstance(parsed, list)
        or not all(isinstance(item, str) for item in parsed)
    ):
        raise HTTPException(
            status_code=400,
            detail="profile_urls must contain a JSON array of strings.",
        )
    return [item.strip() for item in parsed if item.strip()]


def _initial_state(
    profile: dict[str, Any],
    documents: list[dict[str, Any]],
    profile_urls: list[str],
) -> dict[str, Any]:
    return {
        "student_profile": profile,
        "documents": documents,
        "profile_urls": profile_urls,
        "profile_valid": False,
        "profile_evidence": [],
        "opportunities": [],
        "evidence": [],
        "extraction_metadata": {},
        "eligibility_results": [],
        "shortlist": [],
        "review": {},
        "application_draft": "",
        "agent_status": {
            "profile_intelligence": "pending",
            "supervisor": "pending",
            "opportunity_hunter": "pending",
            "eligibility_evidence_auditor": "pending",
            "matchmaker": "pending",
            "recommendation_reviewer": "pending",
            "application_coach": "pending",
        },
        "errors": [],
        "supervisor_retries": 0,
        "supervisor_retry_counts": {},
        "supervisor_steps": 0,
        "supervisor_decision": {},
    }


async def _read_workflow_inputs(
    profile: str,
    profile_urls: str,
    documents: list[UploadFile] | None,
) -> dict[str, Any]:
    parsed_profile = _parse_json_object(profile, "profile")
    _validate_profile_inputs(parsed_profile)
    parsed_urls = _parse_url_list(profile_urls)
    document_values = []

    for document in documents or []:
        if not document.filename:
            raise HTTPException(
                status_code=400,
                detail="Every uploaded document must have a filename.",
            )
        document_values.append({
            "filename": document.filename,
            "content": await document.read(),
        })

    return _initial_state(parsed_profile, document_values, parsed_urls)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/workflow")
async def run_workflow(
    profile: str = Form(..., description="Student profile as a JSON object."),
    profile_urls: str = Form(
        "[]",
        description="Profile URLs as a JSON array of strings.",
    ),
    documents: list[UploadFile] | None = File(
        None,
        description="Optional resume, marksheet, or supporting PDFs.",
    ),
) -> dict[str, Any]:
    state = await _read_workflow_inputs(profile, profile_urls, documents)

    result = await run_in_threadpool(
        scholarship_graph.invoke,
        state,
        {"run_name": "ScholarAI workflow"},
    )

    return {
        "profile_valid": result["profile_valid"],
        "student_profile": result["student_profile"],
        "profile_evidence": result["profile_evidence"],
        "shortlist": result["shortlist"],
        "eligibility_results": result.get("eligibility_results", []),
        "review": result["review"],
        "application_draft": result["application_draft"],
        "supervisor_decision": result.get("supervisor_decision", {}),
        "agent_status": result["agent_status"],
        "errors": result["errors"],
    }


@app.post("/workflow/jobs", status_code=202)
async def submit_workflow_job(
    profile: str = Form(..., description="Student profile as a JSON object."),
    profile_urls: str = Form(
        "[]",
        description="Profile URLs as a JSON array of strings.",
    ),
    documents: list[UploadFile] | None = File(None),
) -> dict[str, str]:
    state = await _read_workflow_inputs(profile, profile_urls, documents)
    job_id = submit_job(state)
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/workflow/jobs/{job_id}",
    }


@app.get("/workflow/jobs/{job_id}")
def workflow_job_status(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Workflow job not found.")
    return job
