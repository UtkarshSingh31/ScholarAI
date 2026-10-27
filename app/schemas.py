
from typing import Literal
from pydantic import BaseModel, Field


class StudentProfileFacts(BaseModel):
    """Structured facts extracted from student-provided information."""

    name: str | None = None
    nationality: str | None = None
    country_of_residence: str | None = None
    birth_year: int | None = None
    degree: str | None = None
    current_degree_level: str | None = None
    field_of_study: str | None = None
    institution: str | None = None
    cgpa: float | None = None
    cgpa_scale: str | None = None
    graduation_status: str | None = None
    graduation_date: str | None = None
    target_degree_level: str | None = None
    target_field: str | None = None
    target_intake: str | None = None
    preferred_universities: str | None = None
    research_topic: str | None = None
    english_test: str | None = None
    english_score: str | None = None
    work_experience_years: float | None = None
    research_experience: str | None = None
    publications: int | None = None
    admission_status: str | None = None
    funding_need: str | None = None

    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    missing_information: list[str] = Field(default_factory=list)


class RequirementClaim(BaseModel):
    category: Literal[
        "minimum_cgpa",
        "degree_level",
        "field_of_study",
        "nationality",
        "graduation_status",
        "deadline",
        "funding",
        "other",
    ] = Field(description="Category of the extracted fact or requirement.")

    requirement: str = Field(
        description="Requirement or fact explicitly stated by the source."
    )

    value: str = Field(
        description=(
            "Extracted value, such as 7.5, Master's, or India. "
            "Use an empty string when not explicitly stated."
        )
    )

    mandatory: bool = Field(
        description=(
            "True only when the source explicitly identifies this as "
            "a mandatory requirement."
        )
    )

    evidence_quote: str = Field(
        description=(
            "Short, verbatim quotation supporting this claim. "
            "Use an empty string if no supporting quotation exists."
        )
    )


class OpportunityFacts(BaseModel):
    program_name: str = Field(
        description="Program or scholarship name, or empty if unavailable."
    )

    funding_summary: str = Field(
        description="Explicitly stated funding details, or empty if unavailable."
    )

    deadline: str = Field(
        description="Application deadline as stated by the source, or empty if absent."
    )

    claims: list[RequirementClaim] = Field(
        description="Extracted requirements and relevant factual claims."
    )


class RecommendationReview(BaseModel):
    overall_assessment: Literal["supported", "mixed", "insufficient_evidence"]
    concerns: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    required_checks: list[str] = Field(default_factory=list)


class SupervisorDecision(BaseModel):
    next_action: Literal[
        "continue",
        "retry_search",
        "retry_evidence",
        "stop",
    ]
    reason: str
