import asyncio
import math
import time
import httpx
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import async_sessionmaker
from ..models.schemas import BBox
from ..models.db_models import OSMCache
from ..timing_utils import tlog


class OverpassError(Exception):
    """Raised when the Overpass API cannot be reached or returns an error."""
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


# Mirror tried once if the primary endpoint returns a transient error
_MIRROR = "https://overpass.kumi.systems/api/interpreter"


class _RateLimiter:
    """Caps concurrent + per-second outbound Overpass calls (their fair-use policy asks
    for at most 2 concurrent connections, spaced out rather than fired in a burst)."""

    def __init__(self, max_concurrent: int = 2, min_interval: float = 1.0):
        self._sem = asyncio.Semaphore(max_concurrent)
        self._min_interval = min_interval
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def __aenter__(self):
        await self._sem.acquire()
        async with self._lock:
            wait = self._last_call + self._min_interval - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
        return self

    async def __aexit__(self, *exc_info):
        self._sem.release()


def _build_query(bb: str, km2: float, timeout: int, force_buildings: bool = False) -> str:
    """Return a single comprehensive Overpass QL query — ALL features, no area tiering.

    Area-based filtering used to scale the feature set down for larger selections. That
    is now enforced at the frontend via a hard selection-size cap (MAX_AREA_KM2), so we
    always fetch the complete feature set for whatever area was selected. ``km2`` and
    ``force_buildings`` are retained for call-site compatibility but no longer alter the
    query (buildings and every road/path class are always included).
    """
    features = f"""
  way["highway"]({bb});
  way["landuse"]({bb});
  way["leisure"]({bb});
  way["natural"]({bb});
  way["building"]({bb});
  way["waterway"]({bb});
  way["railway"]({bb});
  relation["natural"]({bb});
  relation["landuse"]({bb});
  node["place"~"city|town|village|hamlet|suburb|neighbourhood|quarter|island"]({bb});"""
    return f"[out:json][timeout:{timeout}];\n(\n{features}\n);\nout body;\n>;\nout skel qt;\n"


class OSMFetcher:
    """Fetches OSM data via Overpass API with a single-shot mirror fallback."""

    def __init__(self, overpass_endpoint: str, session_factory: async_sessionmaker | None = None):
        self.endpoint = overpass_endpoint
        # Primary first, then mirror (each tried exactly once — no retry loops)
        self._endpoints = [overpass_endpoint] + (
            [_MIRROR] if overpass_endpoint != _MIRROR else []
        )
        self._cache: dict[tuple, tuple[dict, float]] = {}
        self._cache_ttl = 300  # 5-minute TTL so colour regens are instant
        self._rate_limiter = _RateLimiter()
        # Optional Postgres-backed second-level cache — persists across restarts
        # and is shared across horizontally-scaled backend instances, unlike
        # the in-process dict above. Best-effort: DB errors never break a fetch.
        self._session_factory = session_factory

    async def _db_cache_get(self, key: tuple) -> dict | None:
        if self._session_factory is None:
            return None
        west, south, east, north, force_buildings = key
        cutoff = datetime.utcnow() - timedelta(seconds=self._cache_ttl)
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(OSMCache).where(
                        OSMCache.bbox_west == west, OSMCache.bbox_south == south,
                        OSMCache.bbox_east == east, OSMCache.bbox_north == north,
                        OSMCache.force_buildings == force_buildings,
                        OSMCache.fetched_at > cutoff,
                    )
                )
                row = result.scalars().first()
                return row.response if row else None
        except Exception:
            return None

    async def _db_cache_put(self, key: tuple, data: dict) -> None:
        if self._session_factory is None:
            return
        west, south, east, north, force_buildings = key
        now = datetime.utcnow()
        try:
            async with self._session_factory() as session:
                await session.execute(
                    delete(OSMCache).where(
                        OSMCache.bbox_west == west, OSMCache.bbox_south == south,
                        OSMCache.bbox_east == east, OSMCache.bbox_north == north,
                        OSMCache.force_buildings == force_buildings,
                    )
                )
                # Opportunistic eviction so the table doesn't grow unbounded —
                # ponytail: no cron/background job, just piggybacks on writes.
                await session.execute(delete(OSMCache).where(OSMCache.fetched_at < now - timedelta(hours=1)))
                session.add(OSMCache(
                    bbox_west=west, bbox_south=south, bbox_east=east, bbox_north=north,
                    force_buildings=force_buildings, response=data, fetched_at=now,
                ))
                await session.commit()
        except Exception:
            pass

    async def fetch_area(self, bbox: BBox, timeout: int = 60, force_buildings: bool = False) -> dict:
        key = (round(bbox.west, 5), round(bbox.south, 5),
               round(bbox.east, 5), round(bbox.north, 5), force_buildings)
        cached = self._cache.get(key)
        if cached and (time.time() - cached[1] < self._cache_ttl):
            data = cached[0]
            data['_cached'] = True
            return data

        db_data = await self._db_cache_get(key)
        if db_data is not None:
            self._cache[key] = (db_data, time.time())
            db_data['_cached'] = True
            return db_data

        bb = f"{bbox.south},{bbox.west},{bbox.north},{bbox.east}"
        cos_lat = math.cos((bbox.south + bbox.north) / 2 * math.pi / 180)
        km2 = round((bbox.east - bbox.west) * cos_lat * 111.32 * (bbox.north - bbox.south) * 111.32, 2)
        query = _build_query(bb, km2, timeout, force_buildings=force_buildings)
        headers = {"User-Agent": "heart-on-a-sleeve/1.0", "Accept": "*/*"}

        last_error: OverpassError | None = None
        for endpoint in self._endpoints:
            try:
                t0 = time.perf_counter()
                async with self._rate_limiter:
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(connect=10, read=timeout + 5, write=10, pool=5),
                        headers=headers,
                    ) as client:
                        response = await client.post(endpoint, data={"data": query})

                elapsed_ms = (time.perf_counter() - t0) * 1000

                # Transient server errors — try next endpoint
                if response.status_code in (429, 503, 504):
                    last_error = OverpassError(
                        f"Overpass {response.status_code} from {endpoint[-20:]}", response.status_code)
                    tlog("overpass_transient", elapsed_ms,
                         f"status={response.status_code} ep={endpoint[-20:]} km2={km2}")
                    continue

                # Non-transient HTTP error — don't bother trying mirrors
                if not response.is_success:
                    raise OverpassError(
                        f"Overpass returned HTTP {response.status_code}", response.status_code)

                data = response.json()
                tlog("overpass_fetch", elapsed_ms,
                     f"km2={km2} elements={len(data.get('elements', []))} ep={endpoint[-20:]}")
                self._cache[key] = (data, time.time())
                await self._db_cache_put(key, data)
                return data

            except httpx.TimeoutException:
                last_error = OverpassError(
                    f"Overpass timed out after {timeout}s — try a smaller area", 504)
                tlog("overpass_timeout", (time.perf_counter() - t0) * 1000,
                     f"ep={endpoint[-20:]} km2={km2}")
            except httpx.ConnectError:
                last_error = OverpassError(
                    "Cannot reach Overpass API — check network connection", 503)
            except OverpassError:
                raise
            except httpx.HTTPError as e:
                last_error = OverpassError(f"Overpass network error: {e}", 502)

        raise last_error or OverpassError("Overpass fetch failed", 502)

    async def get_license_info(self, bbox: BBox) -> dict:
        return {
            "license": "ODbL",
            "url": "https://www.openstreetmap.org/copyright",
            "attribution_required": True,
            "attribution": "© OpenStreetMap contributors",
            "data_sources": ["OpenStreetMap contributors"],
            "fetched_at": datetime.utcnow().isoformat(),
            "bbox": bbox.model_dump(),
        }