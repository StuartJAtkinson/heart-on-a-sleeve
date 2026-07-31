"""Unit tests for the Postgres-backed OSM cache (OSMFetcher._db_cache_get/_put).

Uses an in-memory SQLite engine so no live DB or network call is needed — the
cache logic itself is plain SQLAlchemy and dialect-agnostic. Run with:
    cd backend && .venv/Scripts/python.exe -m pytest tests/test_osm_cache.py -v
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.database import Base
from app.models.db_models import OSMCache  # noqa: F401 — registers table with Base
from app.models.schemas import BBox
from app.services.osm_fetcher import OSMFetcher

BBOX_KEY = (-2.368, 51.379, -2.350, 51.390, False)


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def test_db_cache_round_trip(session_factory):
    fetcher = OSMFetcher("https://example.invalid", session_factory=session_factory)
    data = {"elements": [{"type": "node", "id": 1}]}

    assert await fetcher._db_cache_get(BBOX_KEY) is None

    await fetcher._db_cache_put(BBOX_KEY, data)
    assert await fetcher._db_cache_get(BBOX_KEY) == data


async def test_db_cache_expires_after_ttl(session_factory):
    fetcher = OSMFetcher("https://example.invalid", session_factory=session_factory)
    fetcher._cache_ttl = 1
    await fetcher._db_cache_put(BBOX_KEY, {"elements": []})

    async with session_factory() as session:
        await session.execute(
            update(OSMCache).where(OSMCache.bbox_west == BBOX_KEY[0]).values(
                fetched_at=datetime.utcnow() - timedelta(seconds=10)
            )
        )
        await session.commit()

    assert await fetcher._db_cache_get(BBOX_KEY) is None


async def test_fetch_area_uses_db_cache_without_network(session_factory):
    """fetch_area must return the DB-cached response without hitting Overpass."""
    fetcher = OSMFetcher("https://example.invalid", session_factory=session_factory)
    bbox = BBox(west=-2.368, south=51.379, east=-2.350, north=51.390)
    data = {"elements": [{"type": "node", "id": 42}]}
    await fetcher._db_cache_put(BBOX_KEY, data)

    result = await fetcher.fetch_area(bbox)
    assert result["elements"] == data["elements"]
    assert result["_cached"] is True
