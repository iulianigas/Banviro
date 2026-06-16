from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.integrations.saltedge_client import SaltEdgeClient, SaltEdgeConfig, SaltEdgeError
from app.models.bank_connection import BankConnection
from app.models.bank_customer import BankCustomer
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.models.user import User

router = APIRouter(prefix="/integrations/revolut", tags=["integrations"])


def _saltedge() -> SaltEdgeClient:
    if not settings.saltedge_app_id or not settings.saltedge_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Salt Edge integration is not configured",
        )
    return SaltEdgeClient(
        SaltEdgeConfig(
            base_url=settings.saltedge_base_url,
            app_id=settings.saltedge_app_id,
            secret=settings.saltedge_secret,
        )
    )


async def _get_or_create_customer(db: Session, user: User) -> BankCustomer:
    existing = (
        db.query(BankCustomer)
        .filter(BankCustomer.user_id == user.id, BankCustomer.provider == "saltedge")
        .first()
    )
    if existing:
        return existing

    client = _saltedge()
    identifier = f"banviro-user-{user.id}"
    try:
        customer_id = await client.create_customer(identifier=identifier)
    except SaltEdgeError as exc:
        raise HTTPException(status_code=502, detail=f"Salt Edge error: {exc}") from exc

    record = BankCustomer(user_id=user.id, provider="saltedge", customer_id=customer_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _ensure_import_category(db: Session, user_id: int, tx_type: TransactionType) -> Category:
    name = "Revolut import"
    category = (
        db.query(Category)
        .filter(
            Category.user_id == user_id,
            Category.type == CategoryType(tx_type.value),
            Category.name == name,
            Category.deleted_at.is_(None),
        )
        .first()
    )
    if category:
        return category

    category = Category(
        name=name,
        type=CategoryType(tx_type.value),
        color="#64748b",
        user_id=user_id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def _parse_amount(value: Any) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


@router.post("/connect")
async def start_connect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    customer = await _get_or_create_customer(db, current_user)
    client = _saltedge()
    try:
        connect_url = await client.create_connect_url(
            customer_id=customer.customer_id,
            return_to=settings.saltedge_return_to_url,
            from_date=(date.today().replace(day=1)).isoformat(),
        )
    except SaltEdgeError as exc:
        raise HTTPException(status_code=502, detail=f"Salt Edge error: {exc}") from exc

    return {"connect_url": connect_url}


@router.post("/complete")
async def complete_connect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    customer = await _get_or_create_customer(db, current_user)
    client = _saltedge()
    try:
        connections = await client.list_connections(customer_id=customer.customer_id)
    except SaltEdgeError as exc:
        raise HTTPException(status_code=502, detail=f"Salt Edge error: {exc}") from exc

    def _score(conn: dict[str, Any]) -> tuple[int, str]:
        provider_name = str(conn.get("provider_name") or conn.get("provider_code") or "").lower()
        is_revolut = 1 if "revolut" in provider_name else 0
        return (is_revolut, str(conn.get("id") or ""))

    connections_sorted = sorted(connections, key=_score)
    if not connections_sorted:
        raise HTTPException(status_code=409, detail="No connections found yet. Try again in a minute.")

    chosen = connections_sorted[-1]
    connection_id = str(chosen.get("id") or "")
    if not connection_id:
        raise HTTPException(status_code=502, detail="Salt Edge connection id missing")

    existing = (
        db.query(BankConnection)
        .filter(BankConnection.user_id == current_user.id, BankConnection.bank == "revolut")
        .first()
    )
    if existing:
        existing.customer_id = customer.customer_id
        existing.connection_id = connection_id
        existing.status = str(chosen.get("status") or chosen.get("stage") or existing.status or "")
        db.commit()
        return {"status": "connected"}

    record = BankConnection(
        user_id=current_user.id,
        provider="saltedge",
        bank="revolut",
        customer_id=customer.customer_id,
        connection_id=connection_id,
        status=str(chosen.get("status") or chosen.get("stage") or ""),
    )
    db.add(record)
    db.commit()
    return {"status": "connected"}


@router.post("/sync")
async def sync_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    conn = (
        db.query(BankConnection)
        .filter(BankConnection.user_id == current_user.id, BankConnection.bank == "revolut")
        .first()
    )
    if not conn:
        raise HTTPException(status_code=409, detail="Revolut is not connected")

    client = _saltedge()
    try:
        accounts = await client.list_accounts(connection_id=conn.connection_id)
    except SaltEdgeError as exc:
        raise HTTPException(status_code=502, detail=f"Salt Edge error: {exc}") from exc

    created = 0
    skipped = 0

    for account in accounts:
        account_id = str(account.get("id") or "")
        if not account_id:
            continue
        try:
            txs = await client.list_transactions(connection_id=conn.connection_id, account_id=account_id)
        except SaltEdgeError as exc:
            raise HTTPException(status_code=502, detail=f"Salt Edge error: {exc}") from exc

        for tx in txs:
            external_id = str(tx.get("id") or "")
            if not external_id:
                continue

            exists = (
                db.query(Transaction)
                .filter(Transaction.user_id == current_user.id, Transaction.external_id == external_id)
                .first()
            )
            if exists:
                skipped += 1
                continue

            amount_raw = _parse_amount(tx.get("amount"))
            if amount_raw < 0:
                tx_type = TransactionType.expense
                amount = -amount_raw
            else:
                tx_type = TransactionType.income
                amount = amount_raw

            category = _ensure_import_category(db, current_user.id, tx_type)

            made_on = str(tx.get("made_on") or "")
            try:
                tx_date = date.fromisoformat(made_on)
            except Exception:
                tx_date = date.today()

            description = str(tx.get("description") or "Revolut transaction")

            db.add(
                Transaction(
                    user_id=current_user.id,
                    category_id=category.id,
                    external_id=external_id,
                    amount=amount,
                    type=tx_type,
                    description=description,
                    transaction_date=tx_date,
                )
            )
            created += 1

    conn.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return {"created": created, "skipped": skipped}
