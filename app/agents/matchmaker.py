from typing import Any
import re

from state import ScholarshipState
from config import MAX_SHORTLIST_SIZE, ordered_allowed_countries

def matchmaker_agent(state: ScholarshipState) -> dict[str, Any]:
    """Rank eligible opportunities using transparent rule-based scoring."""

    profile = state["student_profile"]
    preferred_countries = ordered_allowed_countries(
        profile.get("preferred_countries", [])
    )
    field = profile.get("field_of_study", profile.get("degree", ""))
    degree = profile.get("degree", "")
    budget = str(profile.get("budget", "")).casefold()

    opportunities_by_url = {
        item["source_url"]: item
        for item in state["opportunities"]
        if item.get("source_url")
    }

    ranked = []

    for result in state["eligibility_results"]:
        # Never shortlist an opportunity without a positive eligibility result.
        if result.get("status") != "meets":
            continue

        opportunity = opportunities_by_url.get(
            result.get("source_url"), {}
        )

        score = 0
        reasons = []

        # 1. Country preference: earlier choices receive more points.
        country = opportunity.get("country_searched", "")

        if country in preferred_countries:
            country_score = len(preferred_countries) - (
                preferred_countries.index(country)
            )
            score += country_score
            reasons.append(
                f"Country preference match: {country} (+{country_score})"
            )

        # 2. Field alignment: look for meaningful field terms
        # in the opportunity details and extracted requirements.
        field_terms = {
            word.casefold()
            for word in re.findall(r"[a-z0-9]+", str(field).casefold())
            if len(word) > 2
        }
        degree_terms = {
            word.casefold()
            for word in re.findall(r"[a-z0-9]+", str(degree).casefold())
            if len(word) > 2
        }

        requirements = result.get("requirements", [])
        requirement_text = " ".join(
            str(claim.get("requirement", ""))
            + " "
            + str(claim.get("value", ""))
            for claim in requirements
            if isinstance(claim, dict)
        )

        opportunity_text = " ".join([
            str(opportunity.get("name", "")),
            str(opportunity.get("snippet", "")),
            str(result.get("opportunity_name", "")),
            requirement_text,
        ]).casefold()

        opportunity_words = set(re.findall(r"[a-z0-9]+", opportunity_text))
        matched_terms = sorted(field_terms & opportunity_words)

        if matched_terms:
            score += 3
            reasons.append(
                f"Field alignment: {', '.join(matched_terms)} (+3)"
            )

        matched_degree_terms = sorted(degree_terms & opportunity_words)
        if matched_degree_terms:
            score += 2
            reasons.append(
                "Degree alignment: "
                f"{', '.join(matched_degree_terms)} (+2)"
            )

        # 3. Funding: reward explicit evidence, never penalize missing data.
        funding = result.get("funding_summary", "").casefold()

        if funding.strip():
            score += 1
            reasons.append("Funding information documented (+1)")

            if any(term in funding for term in (
                "fully funded",
                "full tuition",
                "full scholarship",
                "tuition and living",
            )):
                score += 2
                reasons.append("Full funding explicitly indicated (+2)")

            if budget in {"low", "limited", "tight"}:
                score += 1
                reasons.append("Funding supports the stated limited budget (+1)")

        ranked.append({
            **result,
            "ranking_score": score,
            "ranking_reasons": reasons,
        })

    # Highest score first; use name for deterministic tie-breaking.
    ranked.sort(
        key=lambda item: (
            -item["ranking_score"],
            item.get("opportunity_name", "").casefold(),
        )
    )

    return {
        "shortlist": ranked[:MAX_SHORTLIST_SIZE],
        "agent_status": {
            **state.get("agent_status", {}),
            "matchmaker": "completed",
        },
    }
