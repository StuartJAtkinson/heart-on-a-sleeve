"""Programmatic `alembic upgrade head`, safe to run against a DB that was
previously bootstrapped by the old create_all + ad-hoc ALTER TABLE path
(no alembic_version table yet, but the tables already exist).
"""
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"


def _upgrade_sync(connection: Connection) -> None:
    cfg = Config(str(ALEMBIC_INI))
    cfg.attributes["connection"] = connection

    already_versioned = MigrationContext.configure(connection).get_current_revision() is not None
    if not already_versioned and sa_inspect(connection).has_table("users"):
        # Schema already exists from the legacy create_all bootstrap — mark
        # it as caught up to the baseline instead of re-running CREATE TABLE.
        command.stamp(cfg, "head")
    command.upgrade(cfg, "head")


async def run_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(_upgrade_sync)
