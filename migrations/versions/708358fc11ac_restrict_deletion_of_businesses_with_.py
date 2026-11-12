"""Restrict deletion of businesses with customers

Revision ID: 708358fc11ac
Revises: 855027ab3d85
Create Date: 2026-11-11 09:35:53.961792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '708358fc11ac'
down_revision: Union[str, Sequence[str], None] = '855027ab3d85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.drop_constraint(
        "customers_business_id_fkey",
        "customers",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "customers_business_id_fkey",
        "customers",
        "businesses",
        ["business_id"],
        ["id"],
        ondelete="RESTRICT"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "customers_business_id_fkey",
        "customers",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "customers_business_id_fkey",
        "customers",
        "businesses",
        ["business_id"],
        ["id"],
        ondelete="CASCADE"
    )
