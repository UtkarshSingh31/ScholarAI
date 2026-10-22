import os


ALLOWED_COUNTRIES = ("Canada", "Germany", "Singapore")
MAX_SHORTLIST_SIZE = 5
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def ordered_allowed_countries(values: object) -> list[str]:
    """Return only supported countries, in the required priority order."""

    if not isinstance(values, list):
        return []

    normalized = {
        str(value).strip().casefold()
        for value in values
        if str(value).strip()
    }
    return [
        country
        for country in ALLOWED_COUNTRIES
        if country.casefold() in normalized
    ]
