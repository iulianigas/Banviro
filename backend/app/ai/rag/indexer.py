import asyncio

from sqlalchemy.orm import Session, joinedload

from app.ai.logging import ai_logger
from app.ai.rag.retriever import qdrant_retriever
from app.config import settings
from app.i18n.categories import display_category_name
from app.models.transaction import Transaction


def build_transaction_index_text(transaction: Transaction, locale: str = "ro") -> str:
    category_label = display_category_name(
        transaction.category.name,
        transaction.category.slug,
        locale,
    )
    parts = [
        str(transaction.transaction_date),
        transaction.type.value,
        category_label,
        f"{transaction.amount} RON",
    ]
    if transaction.description:
        parts.append(transaction.description.strip())
    return " | ".join(parts)


async def index_transaction(db: Session, transaction_id: int, user_id: int) -> bool:
    transaction = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)
        .first()
    )
    if transaction is None:
        return False

    text = build_transaction_index_text(transaction)
    indexed = await qdrant_retriever.upsert_point(
        point_id=transaction.id,
        text=text,
        user_id=user_id,
        transaction_id=transaction.id,
    )
    if indexed:
        ai_logger.info("indexed transaction_id=%s user_id=%s", transaction_id, user_id)
    return indexed


async def remove_transaction_index(transaction_id: int) -> bool:
    removed = await qdrant_retriever.delete_points([transaction_id])
    if removed:
        ai_logger.info("removed index transaction_id=%s", transaction_id)
    return removed


async def reindex_user_transactions(db: Session, user_id: int) -> int:
    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.id)
        .all()
    )
    indexed = 0
    for transaction in transactions:
        if await index_transaction(db, transaction.id, user_id):
            indexed += 1
    return indexed


def _run_async(coro) -> None:
    asyncio.run(coro)


def schedule_transaction_index(transaction_id: int, user_id: int) -> None:
    if not settings.ai_enabled:
        return

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _run_async(index_transaction(db, transaction_id, user_id))
    except Exception as exc:
        ai_logger.error(
            "background index failed transaction_id=%s user_id=%s: %s",
            transaction_id,
            user_id,
            exc,
        )
    finally:
        db.close()


def schedule_transaction_removal(transaction_id: int) -> None:
    if not settings.ai_enabled:
        return

    try:
        _run_async(remove_transaction_index(transaction_id))
    except Exception as exc:
        ai_logger.error(
            "background index removal failed transaction_id=%s: %s",
            transaction_id,
            exc,
        )
