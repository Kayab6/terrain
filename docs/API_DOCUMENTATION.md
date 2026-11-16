# Phase 4 API

## Optional persistence API

`GET /api/persistence/health` returns:

```json
{
  "success": true,
  "persistence_enabled": true,
  "mongodb_reachable": true,
  "database_configured": true,
  "message": "MongoDB persistence is available"
}
```

`GET /api/persistence/status` reports whether MongoDB persistence is enabled,
connected, and whether active storage is MongoDB or memory.

Saved routes and evacuation scenarios support:

- `GET /api/persistence/<routes|scenarios>`
- `POST /api/persistence/<routes|scenarios>`
- `GET /api/persistence/<routes|scenarios>/<id>`
- `PUT /api/persistence/<routes|scenarios>/<id>`
- `DELETE /api/persistence/<routes|scenarios>/<id>`

Storage failures return HTTP 503 with the standard JSON error format. The
memory fallback is process-local and is reported as such.

## Multiple alternatives

`POST /api/routes/multiple`

```json
{
  "start": [86.925, 27.9881],
  "destination": [86.94, 28.00],
  "algorithm": "astar",
  "preference": "shortest",
  "count": 3
}
```

Count is limited to 1 through 10. Each alternative includes GeoJSON, node IDs, metrics, safety score,
explored nodes, execution time, rank, and recommended status.

## Multi-stop route

`POST /api/routes/multi-stop`

```json
{
  "start": [86.925, 27.9881],
  "stops": [[86.93, 27.99]],
  "destination": [86.94, 28.00],
  "preference": "shortest_total_distance",
  "strategy": "auto"
}
```

Preferences include `shortest_total_distance`, `fastest_total_time`, `lowest_total_elevation`, and
`safest_total_route`. Strategies include `auto`, `exact`, and `greedy`.

## Emergency evacuation

- `POST /api/evacuation/analyze`
- `POST /api/evacuation/validate`
- `POST /api/evacuation/preview`

An analysis request contains `dangerZones`, `shelters`, optional `blockedRoads` and `floodZones`, an evacuation
preference, and `max_flow` algorithm selection. Point locations use `[longitude, latitude]`; danger zones may use
GeoJSON Polygon geometry. Successful analysis returns capacity assignments, evacuation GeoJSON, bottlenecks,
critical min-cut edges, disconnected regions, execution statistics, and warnings.
