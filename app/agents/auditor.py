from typing import Any
import re

from app.state import ScholarshipState
from app.tools import extract_requirements


def _normalized_words(value: object) -> set[str]:
    normalized = str(value).casefold().replace("'s", "s")
    return set(re.findall(r"[a-z0-9]+", normalized))


def _profile_claim_matches(
    category: str,
    claim_value: str,
    profile: dict[str, Any],
) -> bool | None:
    if category == "degree_level":
        profile_value = profile.get(
            "target_degree_level",
            profile.get("degree"),
        )
    elif category == "field_of_study":
        profile_value = profile.get(
            "target_field",
            profile.get("field_of_study"),
        )
    elif category == "graduation_status":
        profile_value = profile.get("graduation_status")
    else:
        return None

    if not profile_value or not claim_value:
        return None

    profile_words = _normalized_words(profile_value)
    claim_words = _normalized_words(claim_value)
    if category == "degree_level":
        degree_aliases = (
            {"master", "masters"},
            {"bachelor", "bachelors"},
            {"doctorate", "doctoral", "phd"},
        )
        for aliases in degree_aliases:
            if profile_words & aliases and claim_words & aliases:
                profile_words = profile_words | aliases
                claim_words = claim_words | aliases
    return bool(profile_words and claim_words and (
        claim_words <= profile_words or profile_words <= claim_words
    ))


def eligibility_auditor_agent(state: ScholarshipState) -> dict[str, Any]:
    """Extract scholarship requirements and evaluate supported claims."""

    results = []
    errors = list(state["errors"])
    profile = state["student_profile"]

    evidence_by_url = {
        item["source_url"]: item
        for item in state.get("evidence", [])
        if item.get("source_url")
    }

    for opportunity in state["opportunities"]:
        name = opportunity.get("name", "Unnamed opportunity")
        url = opportunity.get("source_url", "")
        if not url:
            results.append({
                "opportunity_name": name,
                "source_url": "",
                "status": "unknown",
                "reason": "Opportunity has no source URL.",
                "requirements": [],
            })
            continue

        evidence = evidence_by_url.get(url)

        if not evidence or not evidence.get("raw_content", "").strip():
            results.append({
                "opportunity_name": name,
                "source_url": url,
                "status": "unknown",
                "reason": "No extracted webpage content is available.",
                "requirements": [],
            })
            continue

        try:
            page_content = evidence["raw_content"]

            facts = extract_requirements(
                source_url=url,
                page_content=page_content,
            )

            # Keep only claims whose quoted evidence occurs on the page.
            normalized_page = " ".join(page_content.casefold().split())
            supported_claims = [
                claim
                for claim in facts.claims
                if claim.evidence_quote.strip()
                and " ".join(
                    claim.evidence_quote.casefold().split()
                ) in normalized_page
            ]

            # Evaluate only mandatory claims where the profile and source
            # provide directly comparable values.
            decisions: list[bool | None] = []
            claim_decisions: dict[int, bool | None] = {}

            for claim_index, claim in enumerate(supported_claims):
                if not claim.mandatory:
                    continue

                if claim.category == "minimum_cgpa":
                    scale_match = re.search(
                        r"(?:out of|/)\s*10(?:\.0+)?\b",
                        claim.evidence_quote,
                        re.IGNORECASE,
                    )
                    score_match = re.search(
                        r"\d+(?:\.\d+)?",
                        claim.value,
                    )
                    profile_scale = str(
                        profile.get("cgpa_scale", "")
                    ).strip()
                    if (
                        scale_match
                        and score_match
                        and profile.get("cgpa") is not None
                        and profile_scale in {"10", "10.0", "10.00"}
                    ):
                        minimum_cgpa = float(score_match.group())
                        decision = profile["cgpa"] >= minimum_cgpa
                        decisions.append(decision)
                        claim_decisions[claim_index] = decision
                    else:
                        decisions.append(None)
                        claim_decisions[claim_index] = None
                    continue

                if claim.category in {
                    "degree_level",
                    "field_of_study",
                    "graduation_status",
                }:
                    decision = _profile_claim_matches(
                        claim.category,
                        claim.value,
                        profile,
                    )
                    decisions.append(decision)
                    claim_decisions[claim_index] = decision
                    continue

                # Mandatory criteria such as nationality cannot be treated
                # as satisfied when the profile has no comparable field.
                decisions.append(None)
                claim_decisions[claim_index] = None

            if any(decision is False for decision in decisions):
                status = "does_not_meet"
                reason = (
                    "The student does not meet at least one mandatory "
                    "requirement."
                )
            degree_evaluated = any(
                claim.category == "degree_level"
                and claim.mandatory
                and claim_decisions.get(index) is not None
                for index, claim in enumerate(supported_claims)
            )
            if (
                decisions
                and degree_evaluated
                and all(decision is True for decision in decisions)
            ):
                status = "meets"
                reason = "All evaluated mandatory requirements are met."
            else:
                status = "unknown"
                reason = (
                    "Target degree-level eligibility was not evaluated; "
                    "the result cannot be marked eligible."
                    if not degree_evaluated
                    else (
                        "At least one mandatory requirement is not directly "
                        "comparable with the available student profile."
                    )
                )

            requirements = []
            for claim_index, claim in enumerate(supported_claims):
                requirement = claim.model_dump()
                requirement["decision"] = (
                    "not_evaluated"
                    if not claim.mandatory
                    else (
                        "meets"
                        if claim_decisions.get(claim_index) is True
                        else (
                            "does_not_meet"
                            if claim_decisions.get(claim_index) is False
                            else "unknown"
                        )
                    )
                )
                requirements.append(requirement)

            results.append({
                "opportunity_name": facts.program_name or name,
                "source_url": url,
                "status": status,
                "reason": reason,
                "requirements": requirements,
                "funding_summary": facts.funding_summary,
                "deadline": facts.deadline,
            })

        except Exception as exc:
            errors.append(
                f"Eligibility extraction failed for {name}: "
                f"{type(exc).__name__}: {exc}"
            )

            results.append({
                "opportunity_name": name,
                "source_url": url,
                "status": "unknown",
                "reason": "Requirement extraction failed.",
                "requirements": [],
            })

    return {
        "eligibility_results": results,
        "errors": errors,
        "agent_status": {
            **state.get("agent_status", {}),
            "eligibility_evidence_auditor": "completed",
        },
    }
