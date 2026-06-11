"""Add categories and transactions

Revision ID: 002
Revises: 001
Create Date: 2026-06-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CATEGORIES = [
    ("Salariu", "income", "#16a34a"),
    ("Freelance", "income", "#059669"),
    ("Investiții", "income", "#0d9488"),
    ("Alte venituri", "income", "#14b8a6"),
    ("Chirie", "expense", "#dc2626"),
    ("Mâncare", "expense", "#ea580c"),
    ("Transport", "expense", "#d97706"),
    ("Utilități", "expense", "#ca8a04"),
    ("Shopping", "expense", "#9333ea"),
    ("Sănătate", "expense", "#db2777"),
    ("Divertisment", "expense", "#2563eb"),
    ("Altele", "expense", "#64748b"),
]


def upgrade() -> None:
    bind = op.get_bind()
    category_enum = postgresql.ENUM("income", "expense", name="categorytype")
    transaction_enum = postgresql.ENUM("income", "expense", name="transactiontype")
    category_enum.create(bind, checkfirst=True)
    transaction_enum.create(bind, checkfirst=True)

    category_type = postgresql.ENUM(
        "income", "expense", name="categorytype", create_type=False
    )
    transaction_type = postgresql.ENUM(
        "income", "expense", name="transactiontype", create_type=False
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", category_type, nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("type", transaction_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_transactions_transaction_date"), "transactions", ["transaction_date"], unique=False
    )

    categories_table = sa.table(
        "categories",
        sa.column("name", sa.String),
        sa.column("type", category_type),
        sa.column("color", sa.String),
        sa.column("user_id", sa.Integer),
    )
    op.bulk_insert(
        categories_table,
        [
            {"name": name, "type": cat_type, "color": color, "user_id": None}
            for name, cat_type, color in DEFAULT_CATEGORIES
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_transaction_date"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("categories")
    postgresql.ENUM(name="transactiontype").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="categorytype").drop(op.get_bind(), checkfirst=True)
