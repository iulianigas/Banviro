from datetime import date

from sqlalchemy.orm import Session

from app.i18n.categories import SYSTEM_CATEGORY_LABELS, display_category_name
from app.services.analytics import (
    get_budget_progress,
    get_spending_by_category,
    get_summary_stats,
    list_user_transactions,
)

FINANCE_TOOL_NAMES = (
    "get_summary",
    "list_transactions",
    "get_budgets",
    "get_spending_by_category",
)


def get_finance_tool_definitions() -> list[dict[str, str]]:
    return [
        {
            "name": "get_summary",
            "description": "Returnează sold, venituri, cheltuieli și economii pentru luna curentă.",
        },
        {
            "name": "list_transactions",
            "description": "Listează tranzacțiile recente ale utilizatorului.",
        },
        {
            "name": "get_budgets",
            "description": "Returnează progresul bugetelor lunare pe categorii.",
        },
        {
            "name": "get_spending_by_category",
            "description": "Returnează cheltuielile lunii curente grupate pe categorie.",
        },
    ]


def _target_month_year(month: int | None, year: int | None) -> tuple[int, int]:
    today = date.today()
    return month or today.month, year or today.year


def run_get_summary(
    db: Session,
    user_id: int,
    locale: str,
    *,
    month: int | None = None,
    year: int | None = None,
) -> str:
    target_month, target_year = _target_month_year(month, year)
    summary = get_summary_stats(db, user_id, target_month, target_year)
    if locale == "en":
        return (
            f"Total balance: {summary.balance} RON. "
            f"Current month income: {summary.month_income} RON. "
            f"Current month expenses: {summary.month_expenses} RON. "
            f"Current month savings: {summary.month_savings} RON."
        )
    return (
        f"Sold total: {summary.balance} RON. "
        f"Venituri luna curentă: {summary.month_income} RON. "
        f"Cheltuieli luna curentă: {summary.month_expenses} RON. "
        f"Economii luna curentă: {summary.month_savings} RON."
    )


def run_list_transactions(
    db: Session,
    user_id: int,
    locale: str,
    limit: int = 20,
    *,
    month: int | None = None,
    year: int | None = None,
) -> str:
    target_month, target_year = _target_month_year(month, year)
    transactions = list_user_transactions(
        db,
        user_id,
        limit=limit,
        month=target_month,
        year=target_year,
    )
    if not transactions:
        return "No recent transactions." if locale == "en" else "Nicio tranzacție recentă."

    lines = []
    for tx in transactions:
        category_label = display_category_name(tx.category.name, tx.category.slug, locale)
        lines.append(
            f"- {tx.transaction_date} | {tx.type.value} | {category_label} | "
            f"{tx.amount} RON | {tx.description or ''}"
        )
    return "\n".join(lines)


def run_get_budgets(
    db: Session,
    user_id: int,
    locale: str,
    *,
    month: int | None = None,
    year: int | None = None,
) -> str:
    target_month, target_year = _target_month_year(month, year)
    budgets = get_budget_progress(db, user_id, target_month, target_year)
    if not budgets:
        return (
            "No budgets set for the current month."
            if locale == "en"
            else "Niciun buget setat pentru luna curentă."
        )

    lines = []
    for budget in budgets:
        category_label = display_category_name(
            budget.category_name,
            budget.category_slug,
            locale,
        )
        if locale == "en":
            lines.append(
                f"- {category_label}: spent {budget.spent_amount}/{budget.budget_amount} RON "
                f"({budget.usage_percent}% used, {budget.remaining_amount} RON left)"
            )
        else:
            lines.append(
                f"- {category_label}: cheltuit {budget.spent_amount}/{budget.budget_amount} RON "
                f"({budget.usage_percent}% utilizat, {budget.remaining_amount} RON rămas)"
            )
    return "\n".join(lines)


def run_get_spending_by_category(
    db: Session,
    user_id: int,
    locale: str,
    *,
    month: int | None = None,
    year: int | None = None,
) -> str:
    target_month, target_year = _target_month_year(month, year)
    breakdown = get_spending_by_category(db, user_id, target_month, target_year)
    if not breakdown:
        return (
            "No category spending for the current month."
            if locale == "en"
            else "Nicio cheltuială pe categorii luna curentă."
        )

    lines = []
    for item in breakdown:
        category_label = display_category_name(
            item.category_name,
            item.category_slug,
            locale,
        )
        if locale == "en":
            lines.append(f"- {category_label}: {item.amount} RON")
        else:
            lines.append(f"- {category_label}: {item.amount} RON")
    return "\n".join(lines)


def _category_keywords() -> tuple[str, ...]:
    keywords: list[str] = []
    for slug, labels in SYSTEM_CATEGORY_LABELS.items():
        keywords.append(slug)
        keywords.append(labels["ro"].lower())
        keywords.append(labels["en"].lower())
    return tuple(keywords)


def finance_tools_for_message(message: str) -> list[str]:
    lowered = message.lower()
    tools: list[str] = []

    finance_keywords = (
        "cheltui",
        "spend",
        "venit",
        "income",
        "sold",
        "balance",
        "bani",
        "money",
        "econom",
        "saving",
        "luna",
        "month",
        "categorie",
        "category",
        "tranzac",
        "transaction",
        "suma",
        "amount",
        "cat ",
        "cât",
        "how much",
    )
    budget_keywords = ("buget", "budget")
    category_keywords = _category_keywords()

    if any(word in lowered for word in finance_keywords):
        tools.extend(["get_summary", "list_transactions", "get_spending_by_category"])

    if any(word in lowered for word in category_keywords):
        for tool_name in ("get_spending_by_category", "list_transactions"):
            if tool_name not in tools:
                tools.append(tool_name)

    if any(word in lowered for word in budget_keywords):
        if "get_budgets" not in tools:
            tools.append("get_budgets")

    return list(dict.fromkeys(tools))


def execute_finance_tool(
    tool_name: str,
    db: Session,
    user_id: int,
    locale: str,
) -> str:
    runners = {
        "get_summary": run_get_summary,
        "list_transactions": run_list_transactions,
        "get_budgets": run_get_budgets,
        "get_spending_by_category": run_get_spending_by_category,
    }
    runner = runners.get(tool_name)
    if runner is None:
        raise ValueError(f"Unknown finance tool: {tool_name}")
    return runner(db, user_id, locale)
