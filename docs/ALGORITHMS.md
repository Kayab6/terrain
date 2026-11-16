# Routing Algorithms

## Graph

Roads and trails are stored in an in-memory adjacency-list graph. Nodes contain geographic coordinates,
elevation, and metadata. Edges contain distance, elevation change, slope, surface, travel time, hazards,
blockage status, and preference-aware cost.

## K-shortest paths

Phase 4 uses Yen's K-shortest paths algorithm. It finds the shortest path, removes one edge at each spur
node, and evaluates complete candidate paths in a bounded priority queue. Duplicate node sequences are
removed before alternatives are returned.

## Multi-stop ordering

Exact mode evaluates permutations for at most `MULTI_STOP_EXACT_THRESHOLD` stop positions. Larger plans use
a nearest-selection greedy strategy. Segments use Dijkstra with the selected route preference. Missing roads,
unreachable checkpoints, and external-provider failures are returned explicitly.

## Emergency evacuation

Emergency routing uses Union-Find to identify connected regions and disconnected danger areas. Dinic's maximum-flow
algorithm models danger-zone demand, road capacity, and shelter capacity. Dijkstra assigns preferred routes from
each danger zone to available shelters. Blocked roads are removed, flooded roads receive scenario penalties or are
blocked according to feature configuration, and invalid graph capacity is rejected.
