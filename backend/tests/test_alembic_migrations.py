"""Verifies `alembic upgrade head` reproduces the ORM-defined schema.
Run with:
    cd backend && python -m pytest tests/test_alembic_migrations.py -v
"""
import os
import subprocess
import sys

from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.models import db_models  # noqa: F401 — registers ORM models with Base

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_alembic_upgrade_head_matches_orm_schema(tmp_path):
    db_path = tmp_path / "alembic_test.db"

    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{db_path}"}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    inspector = inspect(create_engine(f"sqlite:///{db_path}"))
    tables = set(inspector.get_table_names())

    expected = set(Base.metadata.tables.keys())
    assert expected <= tables, f"missing tables after migration: {expected - tables}"
