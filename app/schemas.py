
from typing import Literal
from pydantic import BaseModel, Field


class StudentProfileFacts(BaseModel):
    """Structured facts extracted from student-provided information."""

    name: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    cgpa: float | None = None
    cgpa_scale: str | None = None
    graduation_status: str | None = None

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
