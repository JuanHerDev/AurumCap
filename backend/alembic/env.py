import os
import sys
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# --- Load environment variables ---
# This allows Alembic to access your DATABASE_URL from .env or system environment
load_dotenv()

# --- Adjust the Python path ---
# Ensures Alembic can import modules from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Alembic base configuration ---
config = context.config

# --- Configure logging (optional but recommended for debugging) ---
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Import your SQLAlchemy models ---
# Make sure all models are imported so Alembic can detect schema changes
from app.db.database import Base
from app.models import user, refresh_token, access_log

# --- Set target metadata for autogenerate ---
target_metadata = Base.metadata

# --- Get database connection URL ---
# Priority: Supabase URL (DATABASE_URL) → fallback: SQLALCHEMY_DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URL")

# --- Validate that the URL exists ---
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is not defined. Check your .env or environment variables.")

# --- Force Alembic to use this database URL ---
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# --- Run migrations in 'offline' mode ---
def run_migrations_offline() -> None:
    """
    Runs migrations without an active DB connection.
    This generates SQL scripts instead of applying them directly.
    Useful for CI/CD pipelines or previewing migrations.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,  # Detect changes in column types automatically
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# --- Run migrations in 'online' mode ---
def run_migrations_online() -> None:
    """
    Runs migrations with a live connection to the database.
    This is the most common mode for local development and production.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,      # Detect column type changes
            render_as_batch=True,   # Avoid ALTER TABLE issues (recommended for Supabase/Postgres)
        )

        with context.begin_transaction():
            context.run_migrations()


# --- Determine which mode to run ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
