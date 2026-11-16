from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from algorithms.emergency import DisjointSet, Dinic


SEVERITIES = {"low", "medium", "high", "critical"}
PREFERENCES = {"safest", "shortest", "fastest", "easiest"}


def point(value):
    if not isinstance(value, list) or len(value) != 2:
        return None
    try:
        longitude, latitude = map(float, value)
    except (TypeError, ValueError):
        return None
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        return None
    return [longitude, latitude]


def validate_polygon(value):
    if not isinstance(value, dict) or value.get("type") != "Polygon":
        return False
    rings = value.get("coordinates")
    if not isinstance(rings, list) or not rings or not isinstance(rings[0], list) or len(rings[0]) < 4:
        return False
    ring = rings[0]
    if ring[0] != ring[-1]:
        return False
    return all(point(coordinate) is not None for coordinate in ring)


@dataclass
class DangerZone:
    id: str
    location: list[float] | None = None
    geometry: dict[str, Any] | None = None
    population: int = 0
    severity: str = "medium"
    priority: int = 1
    active: bool = True


@dataclass
class Shelter:
    id: str
    location: list[float]
    name: str = ""
    capacity: float = 0
    available_capacity: float = 0
    accessibility: str = "accessible"
    active: bool = True


@dataclass
class EmergencyScenario:
    danger_zones: list[DangerZone] = field(default_factory=list)
    shelters: list[Shelter] = field(default_factory=list)
    blocked_roads: list[dict[str, Any]] = field(default_factory=list)
    flood_zones: list[dict[str, Any]] = field(default_factory=list)
    preference: str = "safest"
    algorithm: str = "max_flow"


def validate_scenario(payload):
    errors = []
    if not isinstance(payload, dict):
        return ["Request body must be a JSON object"], None
    zones = payload.get("dangerZones", [])
    shelters = payload.get("shelters", [])
    if not isinstance(zones, list) or not zones:
        errors.append("At least one danger zone is required")
    if not isinstance(shelters, list) or not shelters:
        errors.append("At least one shelter is required")

    ids = []
    for index, zone in enumerate(zones if isinstance(zones, list) else []):
        if not isinstance(zone, dict):
            errors.append(f"dangerZones[{index}] must be an object")
            continue
        zone_id = zone.get("id")
        if not isinstance(zone_id, str) or not zone_id:
            errors.append(f"dangerZones[{index}].id is required")
        ids.append(zone_id)
        population = zone.get("population")
        if isinstance(population, bool) or not isinstance(population, (int, float)) or population <= 0:
            errors.append(f"dangerZones[{index}].population must be positive")
        if zone.get("severity", "medium") not in SEVERITIES:
            errors.append(f"dangerZones[{index}] has invalid severity")
        priority = zone.get("priority", 1)
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
            errors.append(f"dangerZones[{index}] has invalid priority")
        location = zone.get("location")
        geometry = zone.get("geometry")
        if geometry is not None and not validate_polygon(geometry):
            errors.append(f"dangerZones[{index}] has invalid polygon geometry")
        if location is not None and point(location) is None:
            errors.append(f"dangerZones[{index}] has invalid coordinates")
        if location is None and geometry is None:
            errors.append(f"dangerZones[{index}] requires location or geometry")

    for index, shelter in enumerate(shelters if isinstance(shelters, list) else []):
        if not isinstance(shelter, dict):
            errors.append(f"shelters[{index}] must be an object")
            continue
        shelter_id = shelter.get("id")
        if not isinstance(shelter_id, str) or not shelter_id:
            errors.append(f"shelters[{index}].id is required")
        ids.append(shelter_id)
        if point(shelter.get("location")) is None:
            errors.append(f"shelters[{index}] has invalid coordinates")
        capacity = shelter.get("capacity")
        if isinstance(capacity, bool) or not isinstance(capacity, (int, float)) or capacity < 0:
            errors.append(f"shelters[{index}] capacity must be non-negative")

    if len(ids) != len(set(ids)):
        errors.append("Danger zone and shelter IDs must be unique")
    if payload.get("preference", "safest") not in PREFERENCES:
        errors.append("Invalid evacuation preference")
    if payload.get("algorithm", "max_flow") != "max_flow":
        errors.append("Only the max_flow evacuation algorithm is supported")
    for name, features in (("blockedRoads", payload.get("blockedRoads", [])), ("floodZones", payload.get("floodZones", []))):
        if not isinstance(features, list):
            errors.append(f"{name} must be an array")
    return errors, EmergencyScenario(
        danger_zones=[],
        shelters=[],
        blocked_roads=payload.get("blockedRoads", []),
        flood_zones=payload.get("floodZones", []),
        preference=payload.get("preference", "safest"),
        algorithm=payload.get("algorithm", "max_flow"),
    )


def emergency_graph_summary(graph):
    disjoint_set = DisjointSet(graph.nodes.keys())
    blocked = 0
    flooded = 0
    for edges in graph.adjacency.values():
        for edge in edges:
            if edge.blocked:
                blocked += 1
            if edge.flood_risk > 0:
                flooded += 1
            if edge.available and not edge.blocked:
                disjoint_set.union(edge.source, edge.destination)
    components = {}
    for node_id in graph.nodes:
        root = disjoint_set.find(node_id)
        components.setdefault(root, []).append(node_id)
    return {
        "nodeCount": graph.node_count(),
        "edgeCount": graph.edge_count(),
        "blockedEdgeCount": blocked,
        "floodAffectedEdgeCount": flooded,
        "reachableComponents": list(components.values()),
    }


def calculate_max_flow(graph, zone_nodes, shelter_nodes, populations, capacities):
    source = len(graph.nodes)
    shelter_offset = source + 1
    sink = shelter_offset + len(shelter_nodes)
    network = Dinic(sink + 1)
    reference_edges = {}
    for index, node_id in enumerate(zone_nodes):
        population = float(populations[index])
        network.add_edge(source, shelter_offset - 1 + index, population, ("zone", index))
    shelter_capacity_start = shelter_offset
    for index, node_id in enumerate(shelter_nodes):
        network.add_edge(shelter_capacity_start + index, sink, float(capacities[index]), ("shelter", index))
    for source_node, edges in graph.adjacency.items():
        for edge in edges:
            capacity = max(0.0, float(edge.capacity if edge.capacity is not None else 0))
            if edge.available and not edge.blocked and capacity > 0:
                reference_edges[(source_node, edge.destination)] = capacity
    network_capacity = max(1.0, sum(populations) / max(len(graph.nodes), 1))
    del network_capacity
    return network.max_flow(source, sink)
