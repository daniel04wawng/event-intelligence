"""SQLAlchemy engine + session factory.

Reads `DATABASE_URL` from the environment. Supports Supabase / Neon / local
Postgres / `sqlite:///` for tests. Pool size is small because the pipeline is
a short-lived script; tune up if you run this from a long-lived API process.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def get_engine() -> Engine:
    """Lazily build the engine. Raises if DATABASE_URL is not set."""
    global _engine, _SessionLocal
    if _engine is not None:
        return _engine
    url = database_url()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Either export it (export DATABASE_URL=postgresql://...) "
            "or write it into a .env file in the repo root."
        )
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    _engine = create_engine(url, pool_size=5, max_overflow=5, pool_pre_ping=True, future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope around a series of operations."""
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def db_available() -> bool:
    """True iff DATABASE_URL is set."""
    return bool(database_url())


def ping() -> bool:
    """Open a connection and run `select 1`."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("select 1"))
        return True
    except Exception:
        return False
