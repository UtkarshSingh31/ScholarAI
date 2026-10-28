from unittest.mock import patch

from app.nodes import application_coach_agent


class FakeResponse:
    content = "Draft statement using only the documented Computer Science project."


def make_state(shortlist=None):
    return {
        "student_profile": {
            "name": "Test Student",
            "degree": "B.Tech CSE",
            "cgpa": 8.2,
            "skills": ["Python"],
            "projects": ["Computer Science project"],
            "achievements": [],
        },
        "shortlist": shortlist if shortlist is not None else [{
            "opportunity_name": "Example Scholarship",
            "source_url": "https://example.org/scholarship",
            "status": "meets",
            "funding_summary": "Full tuition",
            "requirements": [{
                "requirement": "Minimum CGPA",
                "value": "8.0",
                "evidence_quote": "minimum CGPA of 8.0 out of 10",
            }],
        }],
        "evidence": [{
            "source_url": "https://example.org/scholarship",
            "raw_content": "Minimum CGPA of 8.0 out of 10.",
        }],
        "application_draft": "",
        "agent_status": {"application_coach": "pending"},
        "errors": [],
    }


def test_application_coach_generates_grounded_review_draft():
    with patch("app.nodes.ChatGoogleGenerativeAI") as model:
        model.return_value.invoke.return_value = FakeResponse()
        result = application_coach_agent(make_state())

    assert "Computer Science project" in result["application_draft"]
    assert result["agent_status"]["application_coach"] == "completed"
    prompt = model.return_value.invoke.call_args.args[0][1].content
    assert "Never invent achievements" in prompt
    assert "https://example.org/scholarship" in prompt


def test_application_coach_requires_a_recommendation():
    result = application_coach_agent(make_state(shortlist=[]))

    assert result["application_draft"] == ""
    assert result["agent_status"]["application_coach"] == "needs_recommendation"
    assert "no eligible opportunity" in result["errors"][-1]


def test_application_coach_accepts_structured_text_blocks():
    class BlockResponse:
        content = [{"type": "text", "text": "Grounded draft"}]

    with patch("app.nodes.ChatGoogleGenerativeAI") as model:
        model.return_value.invoke.return_value = BlockResponse()
        result = application_coach_agent(make_state())

    assert result["application_draft"] == "Grounded draft"
