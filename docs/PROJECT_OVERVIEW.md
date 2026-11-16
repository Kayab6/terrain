# Project Overview

## Product direction

DepthWizard is being converted into a terrain-aware route, multi-stop, and emergency evacuation optimizer. Phase 1 creates a stable foundation around the existing 3D terrain explorer and separates experimental features from core visualization.

## Phase 1

Included:

- React and TypeScript frontend with Vite.
- Three.js terrain through React Three Fiber and Drei.
- Zustand application state and camera controls.
- Procedural landscape generation.
- Reconstruction progress and terrain inspection UI.
- Isolated prototype assistant component.
- Flask backend application factory and health endpoint.
- CORS support.
- MongoDB environment configuration and reusable connection module.
- Consistent JSON API error structure.
- Backend unit tests.

## Phase 1 is not

- No OpenStreetMap ingestion or routing.
- No Dijkstra or A* implementation.
- No terrain-cost analysis.
- No multi-stop optimizer.
- No emergency evacuation mode.
- No real assistant or route intelligence.

## Phase 2

Phase 2 adds interactive OpenStreetMap location selection and external terrain context. It includes:

- Pan/zoom map navigation.
- Manual start and destination placement with draggable markers.
- Nominatim search and reverse-geocoding endpoints.
- Overpass retrieval of roads and trails as GeoJSON.
- Configurable elevation-provider lookup.
- Frontend mapping from geographic coordinates to the procedural terrain coordinate space.
- Temporary selections kept in browser memory and temporary external API responses.

MongoDB remains intentionally unused. Route optimization algorithms and evacuation features remain out of scope.

## Phase 3

Phase 3 adds custom in-memory routing:

- OSM roads and trails are converted to adjacency-list graph nodes and edges.
- Edges include distance, elevation change, slope, surface, travel time, hazard status, blockage status, and cost.
- BFS, DFS, Dijkstra, and A* run without a third-party routing library.
- Route preferences use configurable distance, elevation, slope, surface, and hazard weights.
- Start and destination coordinates are constrained to nearby graph nodes.
- Calculated routes and route statistics are rendered on MapLibre terrain.

MongoDB, multi-stop planning, multiple routes, and evacuation mode remain outside this phase.

## Phase 4

Phase 4 adds alternative route generation and ordered checkpoints while retaining the Phase 3 single-route
workflow. Yen's algorithm produces distinct terrain-aware alternatives. Multi-stop routes can use exact
permutation optimization for small plans or greedy optimization above the configured threshold.

## Phase 5

Phase 5 provides emergency evacuation planning in memory. It validates danger zones and shelters, applies blocked-road
and flood penalties, detects graph connectivity, assigns shelter capacity, and calculates evacuation routes. The scenario
and results are browser/API ephemeral state and are not persisted.

## Responsibilities

The frontend owns presentation, 3D rendering, local terrain generation, and user interaction. The Flask backend owns API contracts, persistence integration, and future server-side geospatial algorithms. The current frontend and backend can run independently.
