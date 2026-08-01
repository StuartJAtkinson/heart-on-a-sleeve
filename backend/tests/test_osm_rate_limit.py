"""Unit test for the Overpass outbound rate limiter (OSMFetcher._rate_limiter).

Run with:
    cd backend && .venv/Scripts/python.exe -m pytest tests/test_osm_rate_limit.py -v
"""
import asyncio
import time

from app.services.osm_fetcher import _RateLimiter


async def test_rate_limiter_spaces_out_calls():
    limiter = _RateLimiter(max_concurrent=2, min_interval=0.05)

    start = time.monotonic()
    for _ in range(3):
        async with limiter:
            pass
    elapsed = time.monotonic() - start

    # 3 calls with a 0.05s minimum gap must take at least 2 gaps (0.1s)
    assert elapsed >= 0.1


async def test_rate_limiter_caps_concurrency():
    limiter = _RateLimiter(max_concurrent=2, min_interval=0)
    in_flight = 0
    max_in_flight = 0

    async def call():
        nonlocal in_flight, max_in_flight
        async with limiter:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            await asyncio.sleep(0.05)
            in_flight -= 1

    await asyncio.gather(*(call() for _ in range(5)))
    assert max_in_flight <= 2
