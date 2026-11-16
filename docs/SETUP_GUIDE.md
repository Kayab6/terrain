# Setup Guide

## MongoDB persistence

The backend loads `backend/.env` explicitly. Do not place secrets or credentials
in committed files.

MongoDB persistence is disabled by default. The application can run fully in
memory without MongoDB. To enable optional persistence, start MongoDB locally
and set `MONGO_PERSISTENCE_ENABLED=true` in `backend/.env`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MONGO_URI` | `mongodb://127.0.0.1:27017` | MongoDB connection URI |
| `MONGO_DATABASE` | `terrain_optimizer` | Database name |
| `MONGO_SERVER_SELECTION_TIMEOUT_MS` | `3000` | Connection timeout |
| `MONGO_PERSISTENCE_ENABLED` | `false` | Enables MongoDB persistence |

### Windows with a local MongoDB service

1. Install MongoDB Community Server or use an existing local installation.
2. Start the service from an Administrator terminal:
   `net start MongoDB`
3. Verify the port briefly with:
   `Test-NetConnection 127.0.0.1 -Port 27017`
4. In Compass, connect to `mongodb://127.0.0.1:27017`.
5. Start Flask and request `GET http://127.0.0.1:5000/api/persistence/health`.

Compass does not start or provide the database server. If `net start MongoDB`
reports that the service does not exist, install MongoDB and its Windows
service, then start it separately.

When MongoDB is unavailable, startup continues normally, saved items remain
available only in memory, and `GET /api/persistence/status` reports the
degraded backend explicitly. Do not store credentials in committed files.

## Frontend

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Vite normally serves the application at `http://localhost:5173`. Verify the terrain by selecting a landscape and waiting for the reconstruction sequence.

For a production build:

```powershell
npm run build
```

## Backend

From the repository root:

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

The Flask service normally runs at `http://localhost:5000`.

Check it with:

```powershell
Invoke-RestMethod http://localhost:5000/api/health
```

## MongoDB

MongoDB is not required to run the health endpoint. To enable database-backed features:

1. Install and start MongoDB locally, or obtain an approved hosted connection string.
2. Copy `.env.example` to `.env` in the `backend` directory.
3. Set `MONGO_URI` and `MONGO_DATABASE`.
4. Start the Flask service.

Never commit `.env` or credentials. `db.mongo.init_mongo(app)` performs an explicit server ping and raises `MongoConnectionError` when configuration or connectivity fails.

## Backend tests

```powershell
cd backend
python -m pytest
```

## CORS

The Flask API permits browser requests to `/api/*`. Configure allowed origins explicitly before a production deployment instead of using the Phase 1 development setting.

## Phase 2 map configuration

Copy `frontend/.env.example` to `frontend/.env` when the frontend should use a Flask API other than `http://localhost:5000`.

Set the backend variables documented in `backend/.env.example` to use different Nominatim, Overpass, or elevation providers. The default services are:

- Nominatim: `https://nominatim.openstreetmap.org`
- Overpass: `https://overpass-api.de/api/interpreter`
- Elevation: Open-Elevation at `https://api.open-elevation.com/api/v1/lookup`

An external provider failure is returned as an HTTP 502 JSON error. The application does not substitute fabricated success data.

## 3D terrain provider configuration

## MapLibre OpenStreetMap setup

The frontend bundles the MapLibre GL JS worker from the installed package with
Vite. No worker CDN URL or separate local worker file is required.

Copy `frontend/.env.example` to `frontend/.env` when overriding providers:

- `VITE_MAP_STYLE_URL`: MapLibre style JSON URL. The default is
  `/map-styles/osm-3d.json`, which renders OpenStreetMap raster tiles.
- `VITE_MAP_PROVIDER_TOKEN`: optional provider token. It replaces `{token}` in
  style and DEM URLs.
- `VITE_TERRAIN_SOURCE_URL`: raster DEM URL containing `{z}/{x}/{y}`.
- `VITE_API_BASE_URL`: Flask backend URL.

The default style requires the attribution `© OpenStreetMap contributors`.
The default DEM is AWS Terrain Tiles / Mapzen Terrarium data and requires
network access. MapLibre uses a worker URL bundled by Vite and terrain is
configured from `VITE_TERRAIN_SOURCE_URL`; provider failures are shown in the
map error state instead of being replaced with mock tiles.

MapLibre uses `frontend/.env`:

- `VITE_MAP_STYLE_URL`: MapLibre-compatible style JSON URL.
- `VITE_MAP_PROVIDER_TOKEN`: optional token appended where the configured URLs contain `{token}`.
- `VITE_TERRAIN_SOURCE_URL`: raster DEM tile URL, including `{z}/{x}/{y}`.

The default DEM is AWS Terrain Tiles in Terrarium encoding. It provides public SRTM-derived terrain but can require attribution and network availability. MapTiler or Mapbox styles and DEM tiles can also be configured; their terms, tokens, and tile URLs must be supplied explicitly.

Use a pitch between 55 and 65 degrees and zoom over mountainous terrain to verify real elevation. Flat styling alone does not confirm DEM rendering.

## Map workflow

Open a reconstructed terrain, select Start or Destination in the map panel, then click the map or drag a marker. The trash button clears both selections. Data remains in browser memory only and is reset when selections are cleared or the page reloads.

## Phase 2 API

- `GET /api/map/features?south=&west=&north=&east=`
- `GET /api/elevation?lat=&lng=`
- `GET /api/geocode?q=&limit=`
- `GET /api/reverse-geocode?lat=&lng=`

## Phase 3 routing

The backend builds the graph from OSM features in memory for each route request. Configure the nearest-node
limit with `ROUTE_MAX_DISTANCE_METERS`.

Calculate a route with:

```powershell
$body = @{
  start = @(86.925, 27.9881)
  destination = @(86.94, 28.00)
  algorithm = "dijkstra"
  preference = "shortest"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:5000/api/routes/calculate -ContentType application/json -Body $body
```

Supported algorithms are `bfs`, `dfs`, `dijkstra`, and `astar`. Supported preferences are `shortest`, `fastest`,
`easiest`, `lowest_elevation`, and `safest`.
