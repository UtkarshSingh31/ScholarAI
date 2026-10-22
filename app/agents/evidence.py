from typing import Any

from app.state import ScholarshipState
from app.mcp_client import extract_opportunity_pages

EXTRACTION_BATCH_SIZE = 20


def evidence_node(state: ScholarshipState) -> dict[str, Any]:
    """Extract discovered pages and preserve their provenance."""

    opportunities = state["opportunities"]
    urls = list(dict.fromkeys(
        item["source_url"]
        for item in opportunities
        if item.get("source_url")
    ))

    evidence = []
    errors = []
    metadata: dict[str, Any] = {
        "batch_count": 0,
        "requested_url_count": len(urls),
    }

    for start in range(0, len(urls), EXTRACTION_BATCH_SIZE):
        batch = urls[start:start + EXTRACTION_BATCH_SIZE]
        metadata["batch_count"] += 1

        try:
            response = extract_opportunity_pages(batch)
        except Exception as exc:
            errors.append(
                f"Tavily extraction request failed for batch "
                f"{metadata['batch_count']}: "
                f"{type(exc).__name__}: {exc}"
            )
            continue

        for key, value in response.items():
            if key in {"results", "failed_results"}:
                continue
            if key == "response_time":
                metadata[key] = metadata.get(key, 0) + value
            else:
                metadata[key] = value

        for extracted in response.get("results", []):
            source_url = extracted.get("url")
            if not source_url:
                errors.append("Extraction returned a result without a URL.")
                continue

            matching_opportunity = next(
                (
                    item for item in opportunities
                    if item.get("source_url") == source_url
                ),
                {},
            )

            evidence.append({
                "opportunity_name": matching_opportunity.get("name"),
                "source_url": source_url,
                "raw_content": extracted.get("raw_content", ""),
                "verified": False,
            })

        errors.extend(
            f"Extraction failed for {item.get('url')}: "
            f"{item.get('error', 'Unknown extraction error')}"
            for item in response.get("failed_results", [])
        )

    return {
        "evidence": evidence,
        "extraction_metadata": metadata,
        "errors": state["errors"] + errors,
    }
