"""Add Salt Edge customers table.

Revision ID: 007
Revises: 006
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bank_customers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="saltedge"),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_bank_customers_user_provider"),
        sa.UniqueConstraint("provider", "customer_id", name="uq_bank_customers_provider_customer"),
    )
    op.create_index("ix_bank_customers_user_id", "bank_customers", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_bank_customers_user_id", table_name="bank_customers")
    op.drop_table("bank_customers")

