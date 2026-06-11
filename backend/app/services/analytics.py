from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import extract, func
from sqlalchemy.orm import Session, joinedload

from app.models.budget import Budget
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.schemas.finance import (
    BalanceTrendItem,
    BudgetProgressItem,
    CategoryBreakdownItem,
    MonthlyTrendItem,
    SummaryStats,
)


def _month_year_pairs(end_month: int, end_year: int, count: int) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    month = end_month
    year = end_year
    for _ in range(count):
        pairs.append((month, year))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    pairs.reverse()
    return pairs


def _sum_by_type(
    db: Session,
    user_id: int,
    tx_type: TransactionType,
    month: int | None = None,
    year: int | None = None,
    until_date: date | None = None,
) -> Decimal:
    query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == tx_type,
    )
    if month is not None and year is not None:
        query = query.filter(
            extract("month", Transaction.transaction_date) == month,
            extract("year", Transaction.transaction_date) == year,
        )
    if until_date is not None:
        query = query.filter(Transaction.transaction_date <= until_date)
    return Decimal(str(query.scalar()))


def get_summary_stats(
    db: Session,
    user_id: int,
    month: int | None = None,
    year: int | None = None,
) -> SummaryStats:
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    total_income = _sum_by_type(db, user_id, TransactionType.income)
    total_expenses = _sum_by_type(db, user_id, TransactionType.expense)
    month_income = _sum_by_type(
        db, user_id, TransactionType.income, target_month, target_year
    )
    month_expenses = _sum_by_type(
        db, user_id, TransactionType.expense, target_month, target_year
    )

    return SummaryStats(
        balance=total_income - total_expenses,
        month_income=month_income,
        month_expenses=month_expenses,
        month_savings=month_income - month_expenses,
    )


def get_spending_by_category(
    db: Session, user_id: int, month: int, year: int
) -> list[CategoryBreakdownItem]:
    rows = (
        db.query(
            Category.id,
            Category.name,
            Category.color,
            func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.expense,
            extract("month", Transaction.transaction_date) == month,
            extract("year", Transaction.transaction_date) == year,
        )
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    return [
        CategoryBreakdownItem(
            category_id=row.id,
            category_name=row.name,
            color=row.color,
            amount=Decimal(str(row.amount)),
        )
        for row in rows
        if Decimal(str(row.amount)) > 0
    ]


def get_monthly_trend(
    db: Session,
    user_id: int,
    months: int = 6,
    end_month: int | None = None,
    end_year: int | None = None,
) -> list[MonthlyTrendItem]:
    today = date.today()
    target_month = end_month or today.month
    target_year = end_year or today.year
    results: list[MonthlyTrendItem] = []

    for month_index, year in _month_year_pairs(target_month, target_year, months):
        income = _sum_by_type(db, user_id, TransactionType.income, month_index, year)
        expenses = _sum_by_type(db, user_id, TransactionType.expense, month_index, year)
        results.append(
            MonthlyTrendItem(
                month=f"{year}-{month_index:02d}",
                income=income,
                expenses=expenses,
            )
        )

    return results


def get_balance_trend(
    db: Session,
    user_id: int,
    months: int = 6,
    end_month: int | None = None,
    end_year: int | None = None,
) -> list[BalanceTrendItem]:
    today = date.today()
    target_month = end_month or today.month
    target_year = end_year or today.year
    results: list[BalanceTrendItem] = []

    for month_index, year in _month_year_pairs(target_month, target_year, months):
        last_day = monthrange(year, month_index)[1]
        until_date = date(year, month_index, last_day)
        income = _sum_by_type(
            db, user_id, TransactionType.income, until_date=until_date
        )
        expenses = _sum_by_type(
            db, user_id, TransactionType.expense, until_date=until_date
        )
        results.append(
            BalanceTrendItem(
                month=f"{year}-{month_index:02d}",
                balance=income - expenses,
            )
        )

    return results


def get_budget_progress(
    db: Session, user_id: int, month: int, year: int
) -> list[BudgetProgressItem]:
    budgets = (
        db.query(Budget)
        .options(joinedload(Budget.category))
        .filter(Budget.user_id == user_id, Budget.month == month, Budget.year == year)
        .all()
    )

    results: list[BudgetProgressItem] = []
    for budget in budgets:
        category_spent = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == TransactionType.expense,
                extract("month", Transaction.transaction_date) == month,
                extract("year", Transaction.transaction_date) == year,
            )
            .scalar()
        )
        spent_amount = Decimal(str(category_spent))
        remaining = budget.amount - spent_amount
        usage_percent = (
            (spent_amount / budget.amount * Decimal("100")).quantize(Decimal("0.01"))
            if budget.amount > 0
            else Decimal("0")
        )

        results.append(
            BudgetProgressItem(
                id=budget.id,
                category_id=budget.category_id,
                category_name=budget.category.name,
                color=budget.category.color,
                budget_amount=budget.amount,
                spent_amount=spent_amount,
                remaining_amount=remaining,
                usage_percent=usage_percent,
            )
        )

    return sorted(results, key=lambda item: item.usage_percent, reverse=True)


def list_user_transactions(
    db: Session,
    user_id: int,
    limit: int = 20,
    month: int | None = None,
    year: int | None = None,
) -> list[Transaction]:
    query = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == user_id)
    )
    if month is not None and year is not None:
        query = query.filter(
            extract("month", Transaction.transaction_date) == month,
            extract("year", Transaction.transaction_date) == year,
        )

    return query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).limit(limit).all()
