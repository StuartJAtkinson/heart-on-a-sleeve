"""Verifies app.core.migrations.run_migrations() against the two startup
scenarios it has to handle: a brand-new DB, and a DB already bootstrapped
by the legacy create_all path (tables exist, no alembic_version yet).
"""
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Base
from app.core.migrations import run_migrations
from app.models import db_models  # noqa: F401 — registers ORM models with Base


async def test_run_migrations_on_fresh_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'fresh.db'}")
    try:
        await run_migrations(engine)
        async with engine.connect() as conn:
            tables = set(await conn.run_sync(lambda c: inspect(c).get_table_names()))
            rev = (await conn.execute(text("select version_num from alembic_version"))).scalar()
        assert {"users", "design_projects", "osm_cache"} <= tables
        assert rev is not None
    finally:
        await engine.dispose()


async def test_run_migrations_on_legacy_create_all_db(tmp_path):
    """Simulates existing prod: schema already created by create_all, no
    alembic_version table. run_migrations() must stamp instead of re-running
    CREATE TABLE (which would fail on already-existing tables)."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'legacy.db'}")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await run_migrations(engine)  # must not raise

        async with engine.connect() as conn:
            rev = (await conn.execute(text("select version_num from alembic_version"))).scalar()
        assert rev is not None
    finally:
        await engine.dispose()
