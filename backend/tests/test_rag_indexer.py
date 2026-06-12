from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.ai.rag.indexer import build_transaction_index_text
from app.models.transaction import TransactionType


def test_build_transaction_index_text_includes_description() -> None:
    transaction = SimpleNamespace(
        transaction_date=date(2026, 6, 11),
        type=SimpleNamespace(value=TransactionType.expense.value),
        amount=Decimal("150.50"),
        description="Cumpărături Kaufland",
        category=SimpleNamespace(name="Mâncare", slug="food"),
    )

    text = build_transaction_index_text(transaction, locale="ro")

    assert "2026-06-11" in text
    assert "expense" in text
    assert "Mâncare" in text
    assert "150.50 RON" in text
    assert "Cumpărături Kaufland" in text


def test_build_transaction_index_text_uses_english_category_label() -> None:
    transaction = SimpleNamespace(
        transaction_date=date(2026, 6, 11),
        type=SimpleNamespace(value=TransactionType.income.value),
        amount=Decimal("5000.00"),
        description=None,
        category=SimpleNamespace(name="Salariu", slug="salary"),
    )

    text = build_transaction_index_text(transaction, locale="en")

    assert "Salary" in text
    assert "5000.00 RON" in text
