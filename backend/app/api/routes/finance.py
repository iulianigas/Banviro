from datetime import date, datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.ai.rag.indexer import schedule_transaction_index, schedule_transaction_removal
from app.database import get_db
from app.dependencies import get_current_user
from app.models.budget import Budget
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.finance import (
    BalanceTrendItem,
    BudgetProgressItem,
    BudgetUpsert,
    CategoryBreakdownItem,
    CategoryCreate,
    CategoryRead,
    MonthlyTrendItem,
    SummaryStats,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from app.services.analytics import (
    get_balance_trend,
    get_budget_progress,
    get_monthly_trend,
    get_spending_by_category,
    get_summary_stats,
    list_user_transactions,
)

router = APIRouter(tags=["finance"])


def _resolve_period(
    month: int | None, year: int | None
) -> tuple[int, int]:
    today = date.today()
    return month or today.month, year or today.year


def _get_category_for_user(db: Session, category_id: int, user_id: int) -> Category:
    category = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            Category.deleted_at.is_(None),
            (Category.user_id.is_(None)) | (Category.user_id == user_id),
        )
        .first()
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(
    tx_type: TransactionType | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Category]:
    query = db.query(Category).filter(
        Category.deleted_at.is_(None),
        (Category.user_id.is_(None)) | (Category.user_id == current_user.id),
    )
    if tx_type is not None:
        query = query.filter(Category.type == CategoryType(tx_type.value))
    return query.order_by(Category.user_id.is_(None).desc(), Category.name).all()


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Category:
    name = payload.name.strip()
    duplicate = (
        db.query(Category)
        .filter(
            Category.user_id == current_user.id,
            Category.deleted_at.is_(None),
            Category.type == payload.type,
            Category.name.ilike(name),
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a category with this name",
        )

    category = Category(
        name=name,
        type=payload.type,
        color=payload.color,
        user_id=current_user.id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    category = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.deleted_at.is_(None),
        )
        .first()
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    category.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/transactions", response_model=list[TransactionRead])
def list_transactions(
    limit: int = Query(default=20, ge=1, le=100),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Transaction]:
    return list_user_transactions(db, current_user.id, limit, month, year)


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    category = _get_category_for_user(db, payload.category_id, current_user.id)
    if CategoryType(category.type.value) != CategoryType(payload.type.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category type does not match transaction type",
        )

    transaction = Transaction(
        user_id=current_user.id,
        category_id=payload.category_id,
        amount=payload.amount,
        type=payload.type,
        description=payload.description,
        transaction_date=payload.transaction_date,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    background_tasks.add_task(schedule_transaction_index, transaction.id, current_user.id)

    return (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.id == transaction.id)
        .one()
    )


@router.put("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    category = _get_category_for_user(db, payload.category_id, current_user.id)
    if CategoryType(category.type.value) != CategoryType(payload.type.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category type does not match transaction type",
        )

    transaction.category_id = payload.category_id
    transaction.amount = payload.amount
    transaction.type = payload.type
    transaction.description = payload.description
    transaction.transaction_date = payload.transaction_date
    db.commit()
    db.refresh(transaction)

    background_tasks.add_task(schedule_transaction_index, transaction.id, current_user.id)

    return (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.id == transaction.id)
        .one()
    )


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    background_tasks.add_task(schedule_transaction_removal, transaction_id)
    db.delete(transaction)
    db.commit()


@router.get("/analytics/summary", response_model=SummaryStats)
def analytics_summary(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SummaryStats:
    target_month, target_year = _resolve_period(month, year)
    return get_summary_stats(db, current_user.id, target_month, target_year)


@router.get("/analytics/spending-by-category", response_model=list[CategoryBreakdownItem])
def analytics_spending_by_category(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CategoryBreakdownItem]:
    target_month, target_year = _resolve_period(month, year)
    return get_spending_by_category(db, current_user.id, target_month, target_year)


@router.get("/analytics/monthly-trend", response_model=list[MonthlyTrendItem])
def analytics_monthly_trend(
    months: int = Query(default=6, ge=1, le=12),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MonthlyTrendItem]:
    target_month, target_year = _resolve_period(month, year)
    return get_monthly_trend(db, current_user.id, months, target_month, target_year)


@router.get("/analytics/balance-trend", response_model=list[BalanceTrendItem])
def analytics_balance_trend(
    months: int = Query(default=6, ge=1, le=12),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BalanceTrendItem]:
    target_month, target_year = _resolve_period(month, year)
    return get_balance_trend(db, current_user.id, months, target_month, target_year)


@router.get("/budgets", response_model=list[BudgetProgressItem])
def list_budgets(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BudgetProgressItem]:
    target_month, target_year = _resolve_period(month, year)
    return get_budget_progress(db, current_user.id, target_month, target_year)


@router.put("/budgets", response_model=BudgetProgressItem)
def upsert_budget(
    payload: BudgetUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetProgressItem:
    category = _get_category_for_user(db, payload.category_id, current_user.id)
    if category.type != CategoryType.expense:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budgets can only be set for expense categories",
        )

    budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.category_id == payload.category_id,
            Budget.month == payload.month,
            Budget.year == payload.year,
        )
        .first()
    )

    if budget is None:
        budget = Budget(
            user_id=current_user.id,
            category_id=payload.category_id,
            month=payload.month,
            year=payload.year,
            amount=payload.amount,
        )
        db.add(budget)
    else:
        budget.amount = payload.amount

    db.commit()
    db.refresh(budget)

    progress_items = get_budget_progress(db, current_user.id, payload.month, payload.year)
    item = next((entry for entry in progress_items if entry.id == budget.id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Budget error")
    return item


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == current_user.id)
        .first()
    )
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    db.delete(budget)
    db.commit()
