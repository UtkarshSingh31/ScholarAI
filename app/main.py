
from dotenv import load_dotenv

load_dotenv()

from app.graph import scholarship_graph


def run_case(
    profile: dict,
    documents: list[dict] | None = None,
    profile_urls: list[str] | None = None,
) -> None:
    initial_state = {
        "student_profile": profile,
        "documents": documents or [],
        "profile_urls": profile_urls or [],
        "profile_valid": False,
        "profile_evidence": [],
        "opportunities": [],
        "evidence": [],
        "extraction_metadata": {},
        "eligibility_results": [],
        "shortlist": [],
        "review": {},
        "application_draft": "",
        "agent_status": {
            "profile_intelligence": "pending",
            "opportunity_hunter": "pending",
            "eligibility_evidence_auditor": "pending",
            "matchmaker": "pending",
            "application_coach": "pending",
        },
        "errors": [],
    }

    result = scholarship_graph.invoke(initial_state)

    print("\n--- RESULT ---")
    print("Profile valid:", result["profile_valid"])
    print("Normalized profile:", result["student_profile"])
    print("Profile evidence:", result["profile_evidence"])
    print("Opportunities:", [
        item["name"] for item in result["opportunities"]
    ])
    print("Shortlist:", result["shortlist"])
    print("Application draft:", result["application_draft"])
    print("Errors:", result["errors"])


if __name__ == "__main__":
    # Temporary local test input. Real uploads can be passed as bytes.
    student = {
        "name": "Rahul",
        "degree": "B.Tech CSE",
        "cgpa": 8.2,
        "preferred_countries": ["Canada", "Germany", "Singapore"],
        "budget": "low",
    }

    with open("resume.pdf", "rb") as file:
        resume_bytes = file.read()

    with open("marksheet.pdf", "rb") as file:
        marksheet_bytes = file.read()

    run_case(
        profile={
            "preferred_countries": ["Canada", "Germany", "Singapore"],
            "budget": "low",
        },
        documents=[
            {"filename": "resume.pdf", "content": resume_bytes},
            {"filename": "marksheet.pdf", "content": marksheet_bytes},
        ],
        profile_urls=[
            "https://github.com/your-username",
        ],
    )
