# System Architecture

## Optional persistence layer

The Flask application uses a repository abstraction behind the persistence
API. MongoDB repositories persist routes and evacuation scenarios when enabled
and reachable. A thread-safe memory repository remains the fallback and is
used when Phase 6 persistence is disabled. The fallback is not durable across
backend restarts and is reported through `/api/persistence/status`.

## Frontend

```text
LandscapeSelector
  -> generateTerrainData()
  -> Zustand AppStore
  -> ReconstructionOverlay
  -> ThreeCanvas
      -> TerrainMesh
      -> CameraControls
```

Procedural heightmaps and textures are generated in the browser. The Three.js mesh is constructed from the heightmap and may be vertically exaggerated without rebuilding the source data.

The prototype AI assistant is isolated in `frontend/src/components/TerrainAssistant.tsx`. It does not call a backend or model and can be replaced later.

Interactive map selection is provided by `frontend/src/components/MapPanel.tsx`, which uses MapLibre GL JS and a configurable MapLibre style. A configurable raster-DEM source supplies real elevation through MapLibre terrain and hillshade. Selections are temporary React state. Geographic coordinates are converted to terrain coordinates using `frontend/src/utils/coordinates.ts`.

## Backend

```text
backend/app.py
  -> Flask application factory
  -> routes blueprint
  -> db.mongo
  -> services
  -> algorithms (reserved)
```

### API response format

Success responses return JSON such as:

```json
{
  "success": true,
  "message": "Backend is running"
}
```

Request and server errors use:

```json
{
  "success": false,
  "message": "Human-readable error",
  "error": {
    "code": 400,
    "type": "request_error"
  }
}
```

MongoDB is not accessed by the health endpoint. A MongoDB-backed feature must initialize or request the connection through `db.mongo` and handle `MongoConnectionError` explicitly.

## Phase 3 graph and routing

`backend/algorithms/graph.py` contains adjacency-list graph nodes and terrain edges. Custom structures live in
`backend/algorithms/data_structures.py`; `backend/algorithms/routing.py` implements BFS, DFS, Dijkstra, and A*.
`backend/services/route_graph.py` converts OSM GeoJSON to the in-memory graph, validates nearest nodes, and
calculates preference-specific edge costs. `backend/routes/routes.py` exposes route calculation.

The frontend sends the selected coordinates, algorithm, and preference to Flask. The returned GeoJSON LineString
is rendered as the `selected-route` MapLibre source above terrain. Route metrics are displayed beside the controls.

## Phase 5 emergency architecture

Emergency scenarios are validated in `services/emergency.py`. Graph connectivity uses Union-Find in
`algorithms/emergency.py`, while capacity allocation uses the Dinic implementation in the same module.
`routes/evacuation.py` loads an OSM graph, applies scenario blocked/flood state, maps danger zones and shelters
to graph nodes, and uses Dijkstra for evacuation routes. Results are rendered by MapLibre GeoJSON sources and
remain above the DEM terrain.

## Phase 2 external services

`routes/map_data.py` delegates external integration to:

- `services/geocoding.py`: Nominatim-compatible search and reverse geocoding.
- `services/osm_features.py`: Overpass feature retrieval and GeoJSON conversion.
- `services/elevation.py`: configured DEM/elevation provider lookup.
- `services/external_api.py`: shared timeout, HTTP, and JSON validation.
