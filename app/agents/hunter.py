from typing import Any

from state import ScholarshipState
from config import ordered_allowed_countries
from mcp_client import search_opportunities

def opportunity_hunter_agent(state: ScholarshipState) -> dict[str, Any]:
    """Discover scholarship and university-program candidates."""

    profile = state["student_profile"]
    countries = ordered_allowed_countries(
        profile.get("preferred_countries", [])
    )

    current_degree = profile.get("degree", "")
    target_degree = profile.get("target_degree_level", current_degree)
    field = profile.get(
        "target_field",
        profile.get("field_of_study", current_degree),
    )

    opportunities = []
    errors = []
    seen_urls = set()

    for country in countries:
        queries = (
            (
                "scholarships",
                f"official scholarships for international students in "
                f"{field}, {country}. Target degree level: {target_degree}. "
                "Include eligibility, funding, deadlines, and application "
                "pages.",
            ),
            (
                "university funding",
                f"official university funding and funded study programs "
                f"for international students in {field}, {country}. "
                f"Target degree level: {target_degree}. Include scholarships, tuition "
                "waivers, funding details, deadlines, and application pages.",
            ),
        )

        for search_type, query in queries:
            try:
                results = search_opportunities(query, max_results=5)

                for item in results:
                    if not isinstance(item, dict):
                        continue

                    url = str(item.get("source_url", "")).strip()
                    if not url or url in seen_urls:
                        continue

                    name = str(item.get("name", "")).strip()
                    if not name:
                        errors.append(
                            f"Search result without a name skipped for "
                            f"{country} ({search_type})."
                        )
                        continue

                    seen_urls.add(url)
                    opportunities.append({
                        **item,
                        "name": name,
                        "source_url": url,
                        "country_searched": country,
                        "search_type": search_type,
                        "verified": False,
                        "eligibility_status": "unknown",
                    })

            except Exception as exc:
                errors.append(
                    f"Search failed for {country} ({search_type}): "
                    f"{type(exc).__name__}: {exc}"
                )

    if not countries:
        errors.append(
            "No supported destination country was selected. Supported "
            "countries are Canada, Germany, and Singapore."
        )
    elif not opportunities and not errors:
        errors.append("Search completed but returned no usable results.")
    elif len(opportunities) < 10:
        errors.append(
            f"Search found {len(opportunities)} unique opportunities; "
            "fewer than the target of 10 candidates."
        )

    return {
        "opportunities": opportunities,
        "errors": state["errors"] + errors,
        "agent_status": {
            **state.get("agent_status", {}),
            "opportunity_hunter": (
                "completed" if opportunities else "no_results"
            ),
        },
    }
