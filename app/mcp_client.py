import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters, stdio_client


APP_ROOT = Path(__file__).resolve().parent.parent


def _server_parameters() -> StdioServerParameters:
    inherited = {
        key: value
        for key, value in os.environ.items()
        if key in {
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "TEMP",
            "USERPROFILE",
            "TAVILY_API_KEY",
            "GOOGLE_API_KEY",
        }
    }
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        cwd=APP_ROOT,
        env=inherited,
    )


async def _call_tool(name: str, arguments: dict[str, Any]) -> Any:
    async with stdio_client(_server_parameters()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)

    text_parts = [
        item.text
        for item in result.content
        if getattr(item, "type", None) == "text"
    ]
    if not text_parts:
        raise RuntimeError(f"MCP tool {name} returned no text content.")
    return json.loads("".join(text_parts))


def search_opportunities(query: str, max_results: int = 5) -> list[dict]:
    """Call the scholarship search through the local MCP server."""
    result = asyncio.run(_call_tool(
        "search_scholarships",
        {"query": query, "max_results": max_results},
    ))
    if not isinstance(result, list):
        raise ValueError("MCP scholarship search returned an invalid response.")
    return result


def extract_opportunity_pages(urls: list[str]) -> dict:
    """Call opportunity page extraction through the local MCP server."""
    result = asyncio.run(_call_tool(
        "extract_opportunity_pages",
        {"urls": urls},
    ))
    if not isinstance(result, dict):
        raise ValueError("MCP page extraction returned an invalid response.")
    return result
