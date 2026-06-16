"""Add Salt Edge bank connections and transaction external ids.

Revision ID: 006
Revises: 005
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bank_connections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="saltedge"),
        sa.Column("bank", sa.String(length=32), nullable=False, server_default="revolut"),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("connection_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "bank", name="uq_bank_connections_user_bank"),
        sa.UniqueConstraint("provider", "connection_id", name="uq_bank_connections_provider_connection"),
    )
    op.create_index("ix_bank_connections_user_id", "bank_connections", ["user_id"])

    op.add_column("transactions", sa.Column("external_id", sa.String(length=128), nullable=True))
    op.create_index("ix_transactions_external_id", "transactions", ["external_id"])
    op.create_unique_constraint(
        "uq_transactions_user_external_id",
        "transactions",
        ["user_id", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_transactions_user_external_id", "transactions", type_="unique")
    op.drop_index("ix_transactions_external_id", table_name="transactions")
    op.drop_column("transactions", "external_id")

    op.drop_index("ix_bank_connections_user_id", table_name="bank_connections")
    op.drop_table("bank_connections")

