from app.agents import supervisor


def test_supervisor_uses_safe_fallback_when_model_fails(monkeypatch):
    class FailingModel:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(supervisor, "ChatGoogleGenerativeAI", FailingModel)

    result = supervisor.supervisor_agent(
        {
            "profile_valid": True,
            "opportunities": [{"source_url": "https://example.org"}],
            "evidence": [],
            "eligibility_results": [],
            "errors": [],
            "supervisor_retries": 0,
            "agent_status": {},
        },
        "hunter",
    )

    assert result["supervisor_decision"]["next_action"] == "continue"
    assert result["agent_status"]["supervisor"] == "fallback"
    assert "provider unavailable" in result["errors"][0]


def test_supervisor_stops_after_retry_limit(monkeypatch):
    class RetryModel:
        def __init__(self, *args, **kwargs):
            pass

        def with_structured_output(self, *args, **kwargs):
            return self

        def invoke(self, messages):
            return type(
                "Decision",
                (),
                {
                    "next_action": "retry_search",
                    "reason": "Search coverage is weak.",
                    "model_dump": lambda self: {
                        "next_action": self.next_action,
                        "reason": self.reason,
                    },
                },
            )()

    monkeypatch.setattr(supervisor, "ChatGoogleGenerativeAI", RetryModel)

    result = supervisor.supervisor_agent(
        {
            "profile_valid": True,
            "opportunities": [],
            "evidence": [],
            "eligibility_results": [],
            "errors": [],
            "supervisor_retries": 2,
            "supervisor_decision": {"phase": "hunter"},
            "agent_status": {},
        },
        "hunter",
    )

    assert result["supervisor_decision"]["next_action"] == "stop"
    assert result["supervisor_retries"] == 2
