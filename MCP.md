# MCP — map-merch (Heart on a Sleeve)

**Design spec.** No MCP server exists yet.

- **Proposed server:** `map-merch`
- **Transport:** stdio
- **Backs onto:** `backend/app/api/router.py`

## Why this repo wants one

The interesting call here is *what to make*: pick an area, see what OSM actually
has there, and find out whether it will render into something worth printing.
That is a question loop — fetch features, estimate, adjust the bounds — and it
is currently a human clicking a globe.

Generation itself is heavy (SVG, and especially STL), and licensing is a real
constraint, so both get careful treatment below.

## Tools

| Tool | Params | Returns | Backs onto |
|---|---|---|---|
| `fetch_osm_features` | `bbox`, `layers?` | what OSM has in that area | `POST /api/osm/fetch`, `GET /api/osm/features` |
| `reverse_geocode` | `lat`, `lon` | place name for a point | `GET /api/geocode/reverse` |
| `estimate` | `bbox`, `product` | complexity/size estimate before generating | `POST /api/estimate` |
| `check_license` | `bbox` or `feature_set` | whether the data permits the intended use | `POST /api/license/check`, `POST /api/osm/license-info` |
| `generate_svg` | `bbox`, `product`, `options?` | print-ready SVG | `POST /api/generate/svg` |
| `list_projects` | — | saved projects | `backend/app/api/projects.py` |

`estimate` before `generate_*` is the intended order, exactly as
`estimate_sweep_cost` precedes a sweep in travel-planner: it is the cheap way to
discover that a bbox covering half of Yorkshire will not render usefully.

## What must NOT be a tool

- **`POST /api/generate/stl`.** STL generation is the expensive path — mesh work
  over real OSM geometry, tunable, slow. If it is ever exposed it must be
  start/poll with a job id, never a blocking call. `generate_svg` is the cheap
  sibling and answers "what would this look like".
- **All of `backend/app/api/auth.py`** — `register`, `login`, `refresh`,
  `forgot-password`, `reset-password`. Credential flows, without exception.
- **`DELETE /{project_id}`.** Deletes saved work.

## Licensing is not a footnote

OSM data is ODbL, and the output here is **merchandise** — something sold or
given away. `check_license` is a first-class tool for that reason: artwork
generated without the attribution and share-alike position established is
artwork that cannot legally ship.

Any tool that returns generated art should return the licence obligations
alongside it, not leave the caller to remember.

## Implementation note

The OSM fetch and the generators are already separate routes, so the
estimate/generate split this spec leans on exists in the API today. Keep it.
