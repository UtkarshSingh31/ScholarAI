import os

from app import observability


def test_langsmith_is_disabled_without_a_key(monkeypatch):
    monkeypatch.setenv("LANGSMITH_API_KEY", "")
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)

    assert observability.configure_langsmith() is False
    assert "LANGCHAIN_TRACING_V2" not in os.environ


def test_langsmith_sets_standard_tracing_configuration(monkeypatch):
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    monkeypatch.delenv("LANGCHAIN_PROJECT", raising=False)

    try:
        assert observability.configure_langsmith() is True
        assert os.environ["LANGCHAIN_API_KEY"] == "test-key"
        assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
        assert os.environ["LANGCHAIN_PROJECT"] == "ScholarAI"
        assert os.environ["LANGCHAIN_ENDPOINT"] == (
            "https://api.smith.langchain.com"
        )
    finally:
        for key in (
            "LANGCHAIN_TRACING_V2",
            "LANGCHAIN_API_KEY",
            "LANGCHAIN_PROJECT",
            "LANGCHAIN_ENDPOINT",
        ):
            os.environ.pop(key, None)
