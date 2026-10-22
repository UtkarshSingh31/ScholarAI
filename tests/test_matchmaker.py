from app.nodes import matchmaker_agent


def make_state():
    return {
        "student_profile": {
            "preferred_countries": ["Germany", "Canada"],
            "field_of_study": "Computer Science",
            "degree": "Masters",
            "budget": "low",
        },
        "opportunities": [
            {
                "name": "Computer Science Masters Scholarship",
                "source_url": "https://example.org/a",
                "country_searched": "Germany",
                "snippet": "Computer Science funding for Masters students",
            },
            {
                "name": "Unknown Scholarship",
                "source_url": "https://example.org/b",
                "country_searched": "Canada",
            },
        ],
        "eligibility_results": [
            {
                "opportunity_name": "Computer Science Masters Scholarship",
                "source_url": "https://example.org/a",
                "status": "meets",
                "requirements": [],
                "funding_summary": "Fully funded tuition and living costs",
            },
            {
                "opportunity_name": "Unknown Scholarship",
                "source_url": "https://example.org/b",
                "status": "unknown",
                "requirements": [],
                "funding_summary": "Fully funded",
            },
        ],
        "shortlist": [],
        "agent_status": {"matchmaker_application_coach": "pending"},
    }


def test_matchmaker_ranks_supported_match_and_excludes_unknown():
    result = matchmaker_agent(make_state())

    assert len(result["shortlist"]) == 1
    recommendation = result["shortlist"][0]
    assert recommendation["opportunity_name"] == (
        "Computer Science Masters Scholarship"
    )
    assert recommendation["ranking_score"] == 10
    assert any("Country preference match" in reason for reason in recommendation["ranking_reasons"])
    assert any("Full funding" in reason for reason in recommendation["ranking_reasons"])
    assert result["agent_status"]["matchmaker"] == "completed"


def test_matchmaker_caps_shortlist_at_five_and_tie_breaks_by_name():
    state = make_state()
    state["student_profile"] = {}
    state["opportunities"] = []
    state["eligibility_results"] = []

    for index in range(6):
        name = f"Opportunity {index}"
        url = f"https://example.org/{index}"
        state["opportunities"].append({
            "name": name,
            "source_url": url,
            "country_searched": "",
            "snippet": "",
        })
        state["eligibility_results"].append({
            "opportunity_name": name,
            "source_url": url,
            "status": "meets",
            "requirements": [],
            "funding_summary": "",
        })

    result = matchmaker_agent(state)

    assert len(result["shortlist"]) == 5
    assert [item["opportunity_name"] for item in result["shortlist"]] == [
        "Opportunity 0",
        "Opportunity 1",
        "Opportunity 2",
        "Opportunity 3",
        "Opportunity 4",
    ]
