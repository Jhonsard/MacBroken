"""
Environnement Alembic — utilise l'URL sync (psycopg2) et le metadata
de `app.core.database.Base`. Importe `app.models` pour peupler le metadata.
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Rendre `app.*` importable depuis /app ---
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings            # noqa: E402
from app.core.database import Base              # noqa: E402
import app.models  # noqa: F401,E402  — enregistre tous les modèles

config = context.config
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL_SYNC))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()