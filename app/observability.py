import os

from dotenv import load_dotenv


def configure_langsmith() -> bool:
    """Enable LangSmith tracing only when a non-empty API key is configured."""

    load_dotenv()
    api_key = os.getenv("LANGSMITH_API_KEY", "").strip()
    if not api_key:
        return False

    # LangSmith's current Client still reads its credential from the
    # LANGCHAIN_API_KEY compatibility variable.
    os.environ.setdefault("LANGCHAIN_API_KEY", api_key)
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault(
        "LANGCHAIN_PROJECT",
        os.getenv("LANGSMITH_PROJECT", "ScholarAI"),
    )
    os.environ.setdefault(
        "LANGCHAIN_ENDPOINT",
        "https://api.smith.langchain.com",
    )
    return True


LANGSMITH_ENABLED = configure_langsmith()
