"""Add category slugs for i18n of default categories

Revision ID: 004
Revises: 003
Create Date: 2026-06-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_CATEGORY_SLUGS = [
    ("Salariu", "salary"),
    ("Freelance", "freelance"),
    ("Investiții", "investments"),
    ("Alte venituri", "other_income"),
    ("Chirie", "rent"),
    ("Mâncare", "food"),
    ("Transport", "transport"),
    ("Utilități", "utilities"),
    ("Shopping", "shopping"),
    ("Sănătate", "health"),
    ("Divertisment", "entertainment"),
    ("Altele", "other"),
]


def upgrade() -> None:
    op.add_column("categories", sa.Column("slug", sa.String(length=50), nullable=True))
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    connection = op.get_bind()
    for name, slug in SYSTEM_CATEGORY_SLUGS:
        connection.execute(
            sa.text(
                "UPDATE categories SET slug = :slug "
                "WHERE name = :name AND user_id IS NULL"
            ),
            {"name": name, "slug": slug},
        )


def downgrade() -> None:
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_column("categories", "slug")
