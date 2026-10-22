from unittest.mock import patch

from app.agents.reviewer import recommendation_reviewer_agent


class FakeReview:
    def model_dump(self):
        return {
            "overall_assessment": "supported",
            "concerns": [],
            "strengths": ["Eligibility status is supported."],
            "required_checks": ["Confirm the deadline before applying."],
        }


def test_reviewer_annotates_shortlist_with_groq_review():
    state = {
        "student_profile": {"degree": "B.Tech CSE"},
        "shortlist": [{
            "opportunity_name": "Example Scholarship",
            "status": "meets",
            "requirements": [],
        }],
        "agent_status": {"recommendation_reviewer": "pending"},
        "errors": [],
    }

    with patch("app.agents.reviewer.ChatGroq") as groq:
        groq.return_value.with_structured_output.return_value.invoke.return_value = (
            FakeReview()
        )
        result = recommendation_reviewer_agent(state)

    assert result["review"]["status"] == "completed"
    assert result["review"]["overall_assessment"] == "supported"
    assert result["agent_status"]["recommendation_reviewer"] == "completed"


def test_reviewer_skips_when_no_recommendations_exist():
    result = recommendation_reviewer_agent({
        "shortlist": [],
        "agent_status": {},
        "errors": [],
    })

    assert result["review"]["status"] == "skipped"
