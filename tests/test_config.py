from app.config import (
    ALLOWED_COUNTRIES,
    GEMINI_MODEL,
    GROQ_MODEL,
    MAX_SHORTLIST_SIZE,
    ordered_allowed_countries,
)


def test_country_order_is_fixed_and_unsupported_countries_are_removed():
    assert ALLOWED_COUNTRIES == ("Canada", "Germany", "Singapore")
    assert ordered_allowed_countries([
        "Singapore", "India", "Canada", "Germany",
    ]) == ["Canada", "Germany", "Singapore"]


def test_lower_cost_gemini_model_and_top_five_defaults():
    assert GEMINI_MODEL == "gemini-3.5-flash-lite"
    assert MAX_SHORTLIST_SIZE == 5
    assert GROQ_MODEL == "openai/gpt-oss-20b"
