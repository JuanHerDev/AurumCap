"""fix_timezone_consistency

Revision ID: 1e398934f9ec
Revises: 4b0d4ef13bcb
Create Date: 2025-11-24 15:43:17.294801

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e398934f9ec'
down_revision: Union[str, Sequence[str], None] = '4b0d4ef13bcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # 1. Reset timezone configuration if any
    op.execute("RESET timezone")
    
    # 2. Ensure all datetime columns are consistent (without timezone)
    # Investments table is already correct from previous migration
    
    # 3. Fix users table if needed
    op.alter_column('users', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False,
               postgresql_using='created_at::timestamp')
    
    op.alter_column('users', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False,
               postgresql_using='updated_at::timestamp')

def downgrade():
    # Revert changes if needed
    op.alter_column('users', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    
    op.alter_column('users', 'updated_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)