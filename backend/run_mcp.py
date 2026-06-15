#!/usr/bin/env python3
"""Run the Banviro MCP server."""

from __future__ import annotations

import argparse

from app.mcp.server import mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Banviro MCP finance server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="MCP transport (default: stdio for Cursor / Claude Desktop)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host")
    parser.add_argument("--port", type=int, default=8001, help="HTTP bind port")
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
