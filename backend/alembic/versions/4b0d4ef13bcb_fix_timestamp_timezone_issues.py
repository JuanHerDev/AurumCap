"""fix_timestamp_timezone_issues

Revision ID: 4b0d4ef13bcb
Revises: 6866595350b7 
Create Date: 2025-11-24 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4b0d4ef13bcb'
down_revision: Union[str, None] = '6866595350b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ✅ CAMBIAR COLUMNAS DE TIMESTAMP WITH TIME ZONE A TIMESTAMP WITHOUT TIME ZONE
    
    # Para la tabla investments
    op.alter_column('investments', 'date_acquired',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True,
               postgresql_using='date_acquired::timestamp without time zone')
    
    op.alter_column('investments', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False,
               postgresql_using='created_at::timestamp without time zone')
    
    op.alter_column('investments', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False,
               postgresql_using='updated_at::timestamp without time zone')
    
    # Para la tabla users
    op.alter_column('users', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False,
               postgresql_using='created_at::timestamp without time zone')
    
    op.alter_column('users', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=False,
               postgresql_using='updated_at::timestamp without time zone')
    
    # Para la tabla platforms (si existe)
    try:
        op.alter_column('platforms', 'created_at',
                   existing_type=postgresql.TIMESTAMP(timezone=True),
                   type_=sa.DateTime(),
                   existing_nullable=False,
                   postgresql_using='created_at::timestamp without time zone')
        
        op.alter_column('platforms', 'updated_at',
                   existing_type=postgresql.TIMESTAMP(timezone=True),
                   type_=sa.DateTime(),
                   existing_nullable=False,
                   postgresql_using='updated_at::timestamp without time zone')
    except:
        print("⚠️  platforms table or columns not found, skipping...")
        pass
    
    # Para la tabla refresh_tokens (si existe)
    try:
        op.alter_column('refresh_tokens', 'expires_at',
                   existing_type=postgresql.TIMESTAMP(timezone=True),
                   type_=sa.DateTime(),
                   existing_nullable=False,
                   postgresql_using='expires_at::timestamp without time zone')
        
        op.alter_column('refresh_tokens', 'created_at',
                   existing_type=postgresql.TIMESTAMP(timezone=True),
                   type_=sa.DateTime(),
                   existing_nullable=True,
                   postgresql_using='created_at::timestamp without time zone')
    except:
        print("⚠️  refresh_tokens table or columns not found, skipping...")
        pass
    
    # ✅ AGREGAR/ACTUALIZAR DEFAULTS PARA CONSISTENCIA
    op.execute("""
        ALTER TABLE investments 
        ALTER COLUMN date_acquired SET DEFAULT NOW(),
        ALTER COLUMN created_at SET DEFAULT NOW(),
        ALTER COLUMN updated_at SET DEFAULT NOW();
    """)
    
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN created_at SET DEFAULT NOW(),
        ALTER COLUMN updated_at SET DEFAULT NOW();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # ⬇️ REVERTIR LOS CAMBIOS
    
    # Remover defaults primero
    op.execute("""
        ALTER TABLE investments 
        ALTER COLUMN date_acquired DROP DEFAULT,
        ALTER COLUMN created_at DROP DEFAULT,
        ALTER COLUMN updated_at DROP DEFAULT;
    """)
    
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN created_at DROP DEFAULT,
        ALTER COLUMN updated_at DROP DEFAULT;
    """)
    
    # Revertir tipos de columna
    op.alter_column('investments', 'date_acquired',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    
    op.alter_column('investments', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    
    op.alter_column('investments', 'updated_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    
    op.alter_column('users', 'created_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    
    op.alter_column('users', 'updated_at',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=False)
    
    # Revertir platforms (si se modificaron)
    try:
        op.alter_column('platforms', 'created_at',
                   existing_type=sa.DateTime(),
                   type_=postgresql.TIMESTAMP(timezone=True),
                   existing_nullable=False)
        
        op.alter_column('platforms', 'updated_at',
                   existing_type=sa.DateTime(),
                   type_=postgresql.TIMESTAMP(timezone=True),
                   existing_nullable=False)
    except:
        pass
    
    # Revertir refresh_tokens (si se modificaron)
    try:
        op.alter_column('refresh_tokens', 'expires_at',
                   existing_type=sa.DateTime(),
                   type_=postgresql.TIMESTAMP(timezone=True),
                   existing_nullable=False)
        
        op.alter_column('refresh_tokens', 'created_at',
                   existing_type=sa.DateTime(),
                   type_=postgresql.TIMESTAMP(timezone=True),
                   existing_nullable=True)
    except:
        pass