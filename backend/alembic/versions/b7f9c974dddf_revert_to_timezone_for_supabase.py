"""revert_to_timezone_for_supabase

Revision ID: b7f9c974dddf
Revises: 1e398934f9ec
Create Date: 2025-11-24 15:48:30.626459

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7f9c974dddf'
down_revision: Union[str, Sequence[str], None] = '1e398934f9ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # CONVERT ALL COLUMNS TO TIMESTAMP WITH TIME ZONE for Supabase UTC
    
    # Investments table
    op.alter_column('investments', 'date_acquired',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               postgresql_using='date_acquired::timestamp with time zone')
    
    op.alter_column('investments', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using='created_at::timestamp with time zone')
    
    op.alter_column('investments', 'updated_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using='updated_at::timestamp with time zone')
    
    # Tabla users
    op.alter_column('users', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using='created_at::timestamp with time zone')
    
    op.alter_column('users', 'updated_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using='updated_at::timestamp with time zone')

def downgrade():
    # Revert to DateTime without timezone
    op.alter_column('investments', 'date_acquired',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True)
    
    op.alter_column('investments', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False)
    
    op.alter_column('investments', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False)
    
    op.alter_column('users', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False)
    
    op.alter_column('users', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False)