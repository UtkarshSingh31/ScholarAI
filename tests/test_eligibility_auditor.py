from unittest.mock import patch

from app.nodes import eligibility_auditor_agent, evidence_node
from app.schemas import OpportunityFacts, RequirementClaim


def make_state(**overrides):
    state = {
        "student_profile": {
            "degree": "B.Tech CSE",
            "target_degree_level": "masters",
            "target_field": "Computer Science",
            "cgpa": 8.2,
            "cgpa_scale": "10",
        },
        "opportunities": [{
            "name": "Example Scholarship",
            "source_url": "https://example.org/scholarship",
        }],
        "evidence": [{
            "source_url": "https://example.org/scholarship",
            "raw_content": "Applicants must have a minimum CGPA of 8.0 out of 10.",
        }],
        "eligibility_results": [],
        "errors": [],
        "agent_status": {"eligibility_evidence_auditor": "pending"},
    }
    state.update(overrides)
    return state


def test_auditor_marks_supported_cgpa_requirement_as_meets():
    facts = OpportunityFacts(
        program_name="Example Scholarship",
        funding_summary="Full tuition",
        deadline="1 January 2027",
        claims=[RequirementClaim(
            category="minimum_cgpa",
            requirement="Minimum CGPA",
            value="8.0",
            mandatory=True,
            evidence_quote="minimum CGPA of 8.0 out of 10",
        )],
    )

    with patch("app.nodes.extract_requirements", return_value=facts):
        result = eligibility_auditor_agent(make_state())

    assert result["eligibility_results"][0]["status"] == "unknown"
    assert "degree" in result["eligibility_results"][0]["reason"]
    assert result["eligibility_results"][0]["funding_summary"] == "Full tuition"
    assert result["agent_status"]["eligibility_evidence_auditor"] == "completed"


def test_auditor_returns_unknown_without_evidence_or_profile_scale():
    state = make_state(
        evidence=[],
        student_profile={
            "degree": "B.Tech CSE",
            "cgpa": 8.2,
        },
    )

    result = eligibility_auditor_agent(state)

    assert result["eligibility_results"][0]["status"] == "unknown"
    assert "No extracted webpage content" in result["eligibility_results"][0]["reason"]


def test_evidence_node_preserves_successes_and_failures():
    response = {
        "results": [{
            "url": "https://example.org/scholarship",
            "raw_content": "Scholarship requirements",
        }],
        "failed_results": [{
            "url": "https://example.org/other",
            "error": "Unavailable",
        }],
        "response_time": 0.5,
    }

    state = make_state(opportunities=[
        {
            "name": "Example Scholarship",
            "source_url": "https://example.org/scholarship",
        },
        {
            "name": "Other Scholarship",
            "source_url": "https://example.org/other",
        },
    ])

    with patch("app.agents.evidence.extract_opportunity_pages", return_value=response):
        result = evidence_node(state)

    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["source_url"] == (
        "https://example.org/scholarship"
    )
    assert "Unavailable" in result["errors"][-1]


def test_evidence_node_extracts_all_urls_in_batches():
    opportunities = [
        {
            "name": f"Scholarship {index}",
            "source_url": f"https://example.org/{index}",
        }
        for index in range(21)
    ]
    responses = [
        {
            "results": [
                {
                    "url": item["source_url"],
                    "raw_content": f"Requirements {item['name']}",
                }
                for item in opportunities[:20]
            ],
            "failed_results": [],
            "response_time": 1,
        },
        {
            "results": [{
                "url": opportunities[20]["source_url"],
                "raw_content": "Requirements Scholarship 20",
            }],
            "failed_results": [],
            "response_time": 2,
        },
    ]
    state = make_state(opportunities=opportunities)

    with patch(
        "app.agents.evidence.extract_opportunity_pages",
        side_effect=responses,
    ) as extract:
        result = evidence_node(state)

    assert extract.call_count == 2
    assert len(result["evidence"]) == 21
    assert result["extraction_metadata"]["batch_count"] == 2
    assert result["extraction_metadata"]["response_time"] == 3


def test_auditor_evaluates_supported_degree_claim():
    facts = OpportunityFacts(
        program_name="Computer Science Scholarship",
        funding_summary="Tuition support",
        deadline="1 January 2027",
        claims=[RequirementClaim(
            category="degree_level",
            requirement="Applicants must be enrolled in a master's degree",
            value="Master's",
            mandatory=True,
            evidence_quote="master's degree",
        )],
    )
    state = make_state(
        student_profile={
            "degree": "Masters Computer Science",
            "target_degree_level": "masters",
            "field_of_study": "Computer Science",
            "target_field": "Computer Science",
            "cgpa": 8.2,
            "cgpa_scale": "10",
        },
        evidence=[{
            "source_url": "https://example.org/scholarship",
            "raw_content": "Applicants must be enrolled in a master's degree.",
        }],
    )

    with patch("app.nodes.extract_requirements", return_value=facts):
        result = eligibility_auditor_agent(state)

    assert result["eligibility_results"][0]["status"] == "meets"


def test_auditor_preserves_definite_mandatory_failure():
    facts = OpportunityFacts(
        program_name="Computer Science Scholarship",
        funding_summary="Tuition support",
        deadline="1 January 2027",
        claims=[RequirementClaim(
            category="degree_level",
            requirement="Applicants must be enrolled in a PhD",
            value="PhD",
            mandatory=True,
            evidence_quote="enrolled in a PhD",
        )],
    )
    state = make_state(
        student_profile={
            "target_degree_level": "masters",
            "target_field": "Computer Science",
        },
        evidence=[{
            "source_url": "https://example.org/scholarship",
            "raw_content": "Applicants must be enrolled in a PhD.",
        }],
    )

    with patch("app.nodes.extract_requirements", return_value=facts):
        result = eligibility_auditor_agent(state)

    eligibility = result["eligibility_results"][0]
    assert eligibility["status"] == "does_not_meet"
    assert eligibility["requirements"][0]["decision"] == "does_not_meet"


def test_auditor_accepts_verified_program_alignment_without_mandatory_claim():
    facts = OpportunityFacts(
        program_name="Computer Science Master's Scholarship",
        funding_summary="Partial tuition support",
        deadline="1 January 2027",
        claims=[],
    )
    state = make_state(
        student_profile={
            "target_degree_level": "masters",
            "target_field": "Computer Science",
        },
        evidence=[{
            "source_url": "https://example.org/scholarship",
            "raw_content": "Computer Science Master's Scholarship.",
        }],
    )

    with patch("app.nodes.extract_requirements", return_value=facts):
        result = eligibility_auditor_agent(state)

    assert result["eligibility_results"][0]["status"] == "meets"
