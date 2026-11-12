"""Restrict deletion of users and businesses with memberships

Revision ID: 855027ab3d85
Revises: 391bd8aff855
Create Date: 2026-11-11 09:23:47.090126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '855027ab3d85'
down_revision: Union[str, Sequence[str], None] = '391bd8aff855'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.drop_constraint(
        "business_memberships_user_id_fkey",
        "business_memberships",
        type_="foreignkey"
    )

    op.drop_constraint(
        "business_memberships_business_id_fkey",
        "business_memberships",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "business_memberships_user_id_fkey",
        "business_memberships",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT"
    )

    op.create_foreign_key(
        "business_memberships_business_id_fkey",
        "business_memberships",
        "businesses",
        ["business_id"],
        ["id"],
        ondelete="RESTRICT"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "business_memberships_business_id_fkey",
        "business_memberships",
        type_="foreignkey"
    )

    op.drop_constraint(
        "business_memberships_user_id_fkey",
        "business_memberships",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "business_memberships_business_id_fkey",
        "business_memberships",
        "businesses",
        ["business_id"],
        ["id"],
        ondelete="CASCADE"
    )

    op.create_foreign_key(
        "business_memberships_user_id_fkey",
        "business_memberships",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE"
    )