"""MCP finance tools and optional protocol server."""

from app.mcp.tools.finance import execute_finance_tool, get_finance_tool_definitions

__all__ = ["execute_finance_tool", "get_finance_tool_definitions", "get_mcp_server"]


def get_mcp_server():
    """Return the FastMCP server (requires requirements-mcp.txt)."""
    from app.mcp.server import mcp

    return mcp
