import json

from mcp.server.fastmcp import FastMCP

from app.tools import extract_pages, search_web


mcp = FastMCP("ScholarAI")


@mcp.tool()
def search_scholarships(query: str, max_results: int = 5) -> str:
    """Search for scholarship and university funding opportunities."""
    return json.dumps(
        search_web(query, max_results=max_results),
        ensure_ascii=False,
    )


@mcp.tool()
def extract_opportunity_pages(urls: list[str]) -> str:
    """Extract source content and metadata from opportunity URLs."""
    return json.dumps(
        extract_pages(urls),
        ensure_ascii=False,
        default=str,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
