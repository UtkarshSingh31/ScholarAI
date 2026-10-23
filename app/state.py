
from typing import Any, TypedDict


class ScholarshipState(TypedDict):
    # Normalized information about the student
    student_profile: dict[str, Any]
    profile_valid: bool
    documents: list[dict[str, Any]]
    profile_urls: list[str]
    profile_evidence: list[dict[str, Any]]

    # Research and source evidence
    opportunities: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    extraction_metadata: dict[str, Any]

    # Eligibility and recommendations
    eligibility_results: list[dict[str, Any]]
    shortlist: list[dict[str, Any]]
    review: dict[str, Any]

    # Application drafting and workflow monitoring
    application_draft: str
    agent_status: dict[str, str]

    # Errors collected during workflow execution
    errors: list[str]

    # Supervisor routing state
    supervisor_retries: int
    supervisor_retry_counts: dict[str, int]
    supervisor_steps: int
    supervisor_decision: dict[str, Any]
