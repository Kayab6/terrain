# DepthWizard

## Optional MongoDB persistence (Phase 6)

MongoDB is optional. Persistence defaults to memory, so routing and evacuation
continue to work without a database. Enable it in `backend/.env`:

```env
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DATABASE=terrain_optimizer
MONGO_SERVER_SELECTION_TIMEOUT_MS=3000
MONGO_PERSISTENCE_ENABLED=true
```

Place this file at `backend/.env`; the Flask app loads that exact path
regardless of the terminal working directory. MongoDB Compass is only a
client—the MongoDB server service must be running separately.

Persistence status is available from `GET /api/persistence/status`. Saved
routes and evacuation scenarios use `GET/POST /api/persistence/routes`,
`GET/PUT/DELETE /api/persistence/routes/<id>`, and the same `/scenarios`
collection. MongoDB connection failures are reported and the API falls back
to process-local memory instead of silently claiming MongoDB persistence.

DepthWizard is an interactive React, Three.js, and Flask prototype for terrain-aware visualization and future route planning.

## Phase 1 and Phase 2 status

Phase 1 establishes the project foundation:

- Preserves the existing procedural 3D terrain explorer and camera controls.
- Separates the simulated AI chat from terrain rendering.
- Provides independent React/Vite and Flask development servers.
- Adds a Flask health API, consistent JSON errors, CORS, and optional MongoDB configuration.
- Adds backend tests and project documentation.
- Adds an interactive Leaflet/OpenStreetMap location selector.
- Loads roads and trails from Overpass and elevation from a configurable DEM provider.
- Adds Nominatim geocoding endpoints and temporary in-memory selections.
- Adds MapLibre GL JS with configurable raster DEM terrain, terrain exaggeration, hillshade, and 60-degree default camera pitch.

Phase 3 converts in-memory OSM roads and trails into an adjacency-list graph and calculates routes with custom BFS, DFS, Dijkstra, and A* implementations. Routes support shortest, fastest, easiest, lowest-elevation, and safest cost preferences and are rendered on the MapLibre terrain map.

Phase 4 adds Yen K-shortest-path alternatives, multi-stop exact/greedy ordering, route comparison controls, and draggable checkpoint markers.

Phase 5 adds in-memory emergency scenario modeling, danger zones, shelters, blocked/flooded links, Union-Find connectivity,
Dijkstra evacuation routes, Dinic maximum flow, and MapLibre evacuation overlays. MongoDB and scenario persistence remain postponed.

Multi-stop planning, evacuation mode, and MongoDB persistence remain intentionally postponed.

## Structure

```text
frontend/
  src/components/       Terrain, camera, reconstruction, and prototype UI
  src/data/             Curated landscape definitions
  src/store/            Zustand application state
  src/utils/            Procedural terrain and noise generation
backend/
  app.py                Flask application factory
  config.py             Environment configuration
  db/                   MongoDB connection module
  routes/               API routes and JSON error handlers
  services/             Backend services
  algorithms/           Graph structures and custom routing algorithms
  tests/                Flask API and MongoDB tests
docs/
```

## Frontend

Requires Node.js 18 or newer.

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

The map uses the Flask API at `http://localhost:5000` by default. Override it by copying
`frontend/.env.example` to `frontend/.env` and setting `VITE_API_BASE_URL`.

Create a production build with:

```powershell
npm run build
```

## Backend

Requires Python 3.10 or newer.

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Test the health endpoint:

```powershell
Invoke-RestMethod http://localhost:5000/api/health
```

Run backend tests from the `backend` directory:

```powershell
python -m pytest
```

## Environment

Copy [backend/.env.example](backend/.env.example) to `backend/.env`. Do not commit real credentials. MongoDB configuration:

- `MONGO_URI`: MongoDB connection string.
- `MONGO_DATABASE`: database name.
- `PORT`: Flask port; defaults to 5000.
- `NOMINATIM_URL`: Nominatim-compatible service base URL.
- `OVERPASS_URL`: Overpass API endpoint.
- `ELEVATION_URL`: configured elevation provider endpoint.
- `EXTERNAL_API_TIMEOUT`: external HTTP timeout in seconds.
- `ROUTE_MAX_DISTANCE_METERS`: maximum distance from a selection to a route graph node.

MongoDB is optional for the current health endpoint. MongoDB is initialized explicitly by application setup or a future service and failed connections raise a clear `MongoConnectionError`.

See the documents under [docs/](docs/) for detailed setup and architecture information.

## MapLibre real-map setup

## Terrain-Aware Route Optimizer

The application opens directly on the real MapLibre 3D map. Select **Start**
and **Destination** by clicking the map or use place search. Selected points
are reverse-geocoded and elevation sampled through the Flask API, then Dijkstra
or A* calculates a terrain-aware route from real OSM road/trail geometry.

The frontend uses the bundled MapLibre worker from the installed
`maplibre-gl` package; it does not download a worker from a CDN. Configure the
map by copying `frontend/.env.example` to `frontend/.env`:

- `VITE_MAP_STYLE_URL` defaults to the local OpenStreetMap raster style
  `/map-styles/osm-3d.json`.
- `VITE_MAP_PROVIDER_TOKEN` is optional and replaces `{token}` placeholders in
  provider URLs.
- `VITE_TERRAIN_SOURCE_URL` defaults to AWS Terrain Tiles in Terrarium
  encoding.
- `VITE_API_BASE_URL` defaults to the local Flask API.

The built-in style includes OpenStreetMap attribution and map tiles from
`tile.openstreetmap.org`. DEM tiles are loaded from AWS Terrain Tiles, and
MapLibre applies hillshade plus 1.35x terrain exaggeration at a default 60-degree
pitch. Provider, tile, DEM, and worker failures are reported without replacing
the real map with mock data.
