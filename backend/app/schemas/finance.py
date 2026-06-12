from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.category import CategoryType
from app.models.transaction import TransactionType


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str | None = None
    type: CategoryType
    color: str
    user_id: int | None = None


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType
    color: str = Field(default="#64748b", pattern=r"^#[0-9a-fA-F]{6}$")


class TransactionCreate(BaseModel):
    category_id: int
    amount: Decimal = Field(gt=0, decimal_places=2)
    type: TransactionType
    description: str | None = Field(default=None, max_length=500)
    transaction_date: date


class TransactionUpdate(BaseModel):
    category_id: int
    amount: Decimal = Field(gt=0, decimal_places=2)
    type: TransactionType
    description: str | None = Field(default=None, max_length=500)
    transaction_date: date


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    amount: Decimal
    type: TransactionType
    description: str | None
    transaction_date: date
    created_at: datetime
    category: CategoryRead


class SummaryStats(BaseModel):
    balance: Decimal
    month_income: Decimal
    month_expenses: Decimal
    month_savings: Decimal


class CategoryBreakdownItem(BaseModel):
    category_id: int
    category_name: str
    category_slug: str | None = None
    color: str
    amount: Decimal


class MonthlyTrendItem(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal


class BalanceTrendItem(BaseModel):
    month: str
    balance: Decimal


class BudgetUpsert(BaseModel):
    category_id: int
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: Decimal = Field(gt=0, decimal_places=2)


class BudgetProgressItem(BaseModel):
    id: int
    category_id: int
    category_name: str
    category_slug: str | None = None
    color: str
    budget_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    usage_percent: Decimal
