from sqlalchemy.orm import Session

from app.ai.types import ChatContext
from app.i18n.categories import display_category_name
from app.services.analytics import get_summary_stats, list_user_transactions


def _needs_finance_data(message: str) -> bool:
    keywords = (
        "cheltui",
        "spend",
        "venit",
        "income",
        "buget",
        "budget",
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
    )
    lowered = message.lower()
    return any(word in lowered for word in keywords)


def _needs_rag(message: str) -> bool:
    keywords = (
        "de ce",
        "why",
        "explic",
        "explain",
        "analiz",
        "analy",
        "compar",
        "tendin",
        "trend",
        "pattern",
        "sfat",
        "advice",
    )
    lowered = message.lower()
    return any(word in lowered for word in keywords)


async def build_context(
    db: Session,
    user_id: int,
    user_email: str,
    message: str,
    locale: str = "ro",
) -> tuple[ChatContext, list[str]]:
    tools_used: list[str] = []
    context = ChatContext(user_id=user_id, user_email=user_email)

    if _needs_finance_data(message):
        summary = get_summary_stats(db, user_id)
        transactions = list_user_transactions(db, user_id, limit=5)
        if locale == "en":
            context.summary_text = (
                f"Total balance: {summary.balance} RON. "
                f"Current month income: {summary.month_income} RON. "
                f"Current month expenses: {summary.month_expenses} RON. "
                f"Current month savings: {summary.month_savings} RON."
            )
        else:
            context.summary_text = (
                f"Sold total: {summary.balance} RON. "
                f"Venituri luna curentă: {summary.month_income} RON. "
                f"Cheltuieli luna curentă: {summary.month_expenses} RON. "
                f"Economii luna curentă: {summary.month_savings} RON."
            )
        lines = []
        for tx in transactions:
            category_label = display_category_name(tx.category.name, tx.category.slug, locale)
            lines.append(
                f"- {tx.transaction_date} | {tx.type.value} | {category_label} | "
                f"{tx.amount} RON | {tx.description or ''}"
            )
        context.recent_transactions = "\n".join(lines)
        tools_used.append("finance_db")

    return context, tools_used


def should_use_rag(message: str) -> bool:
    return _needs_rag(message)
