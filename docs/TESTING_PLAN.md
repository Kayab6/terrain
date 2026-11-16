# Testing Plan

Run backend tests and frontend checks from the repository:

```powershell
cd backend
python -m pytest
cd ../frontend
npm test
npm run build
```

Backend coverage includes graph structures, custom algorithms, K-shortest paths, API validation, blocked
edges, unreachable routes, and terrain metrics. Frontend coverage includes checkpoint utilities and existing
MapLibre configuration.

Browser verification should confirm alternative routes are distinct, the recommended route is highlighted,
checkpoints can be dragged and reordered, and route overlays remain above MapLibre terrain.

Emergency tests cover scenario validation, Union-Find connectivity, Dinic maximum flow, blocked and flooded edges,
the validate/preview/analyze API contracts, and the expected absence of fake success responses.
