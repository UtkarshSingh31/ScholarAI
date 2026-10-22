from unittest.mock import patch

from app.nodes import opportunity_hunter_agent


def make_state():
    return {
        "student_profile": {
            "degree": "B.Tech CSE",
            "field_of_study": "Computer Science",
            "preferred_countries": ["Germany"],
        },
        "opportunities": [],
        "errors": [],
        "agent_status": {"opportunity_hunter": "pending"},
    }


def test_opportunity_hunter_runs_both_searches_and_deduplicates_urls():
    results = [
        {
            "name": "Scholarship",
            "source_url": "https://example.org/scholarship",
            "snippet": "Funding",
        },
        {
            "name": "Duplicate",
            "source_url": "https://example.org/scholarship",
        },
    ]

    with patch(
        "app.agents.hunter.search_opportunities",
        return_value=results,
    ) as search:
        result = opportunity_hunter_agent(make_state())

    assert search.call_count == 2
    assert len(result["opportunities"]) == 1
    assert result["opportunities"][0]["country_searched"] == "Germany"
    assert result["opportunities"][0]["verified"] is False
    assert result["agent_status"]["opportunity_hunter"] == "completed"
    assert any("fewer than the target of 10" in error for error in result["errors"])


def test_opportunity_hunter_preserves_partial_results_after_search_failure():
    with patch(
        "app.agents.hunter.search_opportunities",
        side_effect=[
            [{"name": "Scholarship", "source_url": "https://example.org/a"}],
            RuntimeError("search unavailable"),
        ],
    ):
        result = opportunity_hunter_agent(make_state())

    assert len(result["opportunities"]) == 1
    assert any("university funding" in error for error in result["errors"])
