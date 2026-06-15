"""Banviro MCP protocol server — exposes finance tools over MCP."""

from typing import Literal

from fastmcp import FastMCP

from app.mcp.deps import mcp_finance_context
from app.mcp.tools.finance import (
    run_get_budgets,
    run_get_spending_by_category,
    run_get_summary,
    run_list_transactions,
)

Locale = Literal["ro", "en"]

mcp = FastMCP(
    name="Banviro Finance",
    instructions=(
        "Personal finance tools for Banviro accounts. "
        "Query balances, transactions, budgets, and category spending. "
        "Requires a valid Banviro JWT access token via BANVIRO_ACCESS_TOKEN."
    ),
)


@mcp.tool
def get_summary(
    locale: Locale = "ro",
    month: int | None = None,
    year: int | None = None,
) -> str:
    """Return total balance plus income, expenses, and savings for a month."""
    with mcp_finance_context() as ctx:
        return run_get_summary(ctx.db, ctx.user.id, locale, month=month, year=year)


@mcp.tool
def list_transactions(
    locale: Locale = "ro",
    month: int | None = None,
    year: int | None = None,
    limit: int = 20,
) -> str:
    """List recent transactions for a month (default: current month)."""
    with mcp_finance_context() as ctx:
        return run_list_transactions(
            ctx.db,
            ctx.user.id,
            locale,
            limit=limit,
            month=month,
            year=year,
        )


@mcp.tool
def get_budgets(
    locale: Locale = "ro",
    month: int | None = None,
    year: int | None = None,
) -> str:
    """Return monthly budget progress grouped by category."""
    with mcp_finance_context() as ctx:
        return run_get_budgets(ctx.db, ctx.user.id, locale, month=month, year=year)


@mcp.tool
def get_spending_by_category(
    locale: Locale = "ro",
    month: int | None = None,
    year: int | None = None,
) -> str:
    """Return expense totals grouped by category for a month."""
    with mcp_finance_context() as ctx:
        return run_get_spending_by_category(ctx.db, ctx.user.id, locale, month=month, year=year)
