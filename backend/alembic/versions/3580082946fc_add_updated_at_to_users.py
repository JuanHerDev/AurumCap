"""Add updated_at to users

Revision ID: 3580082946fc
Revises: ec361bf2e634
Create Date: 2025-11-19 11:52:48.534685
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3580082946fc'
down_revision: Union[str, Sequence[str], None] = 'ec361bf2e634'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "updated_at")
