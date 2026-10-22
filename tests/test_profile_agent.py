from unittest.mock import patch

from app.nodes import profile_intelligence_agent
from app.schemas import StudentProfileFacts


def test_profile_agent_extracts_pdf_and_github_content():
    state = {
        "student_profile": {
            "preferred_countries": ["Germany"],
            "budget": "low",
        },
        "documents": [
            {
                "filename": "resume.pdf",
                "content": b"fake pdf bytes",
            }
        ],
        "profile_urls": [
            "https://github.com/example"
        ],
        "profile_valid": False,
        "profile_evidence": [],
        "opportunities": [],
        "evidence": [],
        "extraction_metadata": {},
        "eligibility_results": [],
        "shortlist": [],
        "application_draft": "",
        "agent_status": {"profile_intelligence": "pending"},
        "errors": [],
    }

    facts = StudentProfileFacts(
        name="Test Student",
        degree="B.Tech CSE",
        cgpa=8.2,
        cgpa_scale="10",
        skills=["Python"],
        projects=["Scholarship Finder"],
        achievements=[],
        missing_information=[],
    )

    with (
        patch(
            "app.nodes.extract_pdf_text",
            return_value="Resume text: Python, Scholarship Finder",
        ),
        patch(
            "app.nodes.extract_profile_urls",
            return_value={
                "sources": [{
                    "source_url": "https://github.com/example",
                    "content": "Public GitHub profile with Python projects",
                }],
                "errors": [],
            },
        ),
        patch(
            "app.nodes.extract_student_profile",
            return_value=facts,
        ) as extract_profile,
    ):
        result = profile_intelligence_agent(state)

    assert result["profile_valid"] is True
    assert result["student_profile"]["cgpa"] == 8.2
    assert result["student_profile"]["preferred_countries"] == ["Germany"]

    sources = extract_profile.call_args.kwargs["source_content"]
    assert len(sources) == 2
    assert any("github.com/example" in s["source_url"] for s in sources)