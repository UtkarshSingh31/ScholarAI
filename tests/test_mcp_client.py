from unittest.mock import patch

import mcp_client


def test_search_opportunities_uses_mcp_tool_result():
    with patch(
        "mcp_client._call_tool",
        return_value=[{"name": "Example", "source_url": "https://example.org"}],
    ) as call:
        result = mcp_client.search_opportunities("computer science")

    assert result[0]["name"] == "Example"
    call.assert_called_once_with(
        "search_scholarships",
        {"query": "computer science", "max_results": 5},
    )


def test_extract_opportunity_pages_rejects_invalid_mcp_result():
    with patch(
        "mcp_client._call_tool",
        return_value=[],
    ):
        try:
            mcp_client.extract_opportunity_pages(["https://example.org"])
        except ValueError as exc:
            assert "invalid response" in str(exc)
        else:
            raise AssertionError("Expected invalid MCP response to fail.")
