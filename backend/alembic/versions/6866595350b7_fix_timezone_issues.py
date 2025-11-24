"""Fix timezone issues

Revision ID: 6866595350b7
Revises: 3580082946fc
Create Date: 2025-11-24 12:58:18.800091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6866595350b7'
down_revision: Union[str, Sequence[str], None] = '3580082946fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
