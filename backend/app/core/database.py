"""
Couche base de données — SQLAlchemy 2.0 async + session factory.
Sert de fondation aux modèles, aux CRUD et à Alembic.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Classe de base déclarative — tous les modèles en héritent."""
    pass


# --- Moteur async (FastAPI) ---
engine: AsyncEngine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,  # 30 min — évite les timeouts côté PostgreSQL
)

# --- Session factory async ---
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# ------------------------------------------------------------------
# Moteur sync (Celery / Alembic)
# ------------------------------------------------------------------
from contextlib import contextmanager
from collections.abc import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sync_engine = create_engine(
    str(settings.DATABASE_URL_SYNC),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    echo=False,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False,
)


@contextmanager
def sync_session_scope() -> Iterator[Session]:
    """
    Context manager sync (utilisé par Celery) : commit auto,
    rollback auto en cas d'exception, fermeture garantie.
    """
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dépendance FastAPI — fournit une session async par requête
    avec rollback automatique en cas d'exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Vérifie la connectivité à la base (utilisé par /health/ready)."""
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False