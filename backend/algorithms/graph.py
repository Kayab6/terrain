from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt
from typing import Any

from .data_structures import HashMap, HashSet


def haversine_meters(first, second):
    lat1, lng1 = radians(first[0]), radians(first[1])
    lat2, lng2 = radians(second[0]), radians(second[1])
    lat_delta = lat2 - lat1
    lng_delta = lng2 - lng1
    a = sin(lat_delta / 2) ** 2 + cos(lat1) * cos(lat2) * sin(lng_delta / 2) ** 2
    return 6371000 * 2 * asin(sqrt(a))


@dataclass
class GraphNode:
    id: str
    latitude: float
    longitude: float
    elevation: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self):
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation": self.elevation,
            "metadata": self.metadata,
        }


@dataclass
class GraphEdge:
    source: str
    destination: str
    distance: float
    elevation_change: float
    slope: float
    surface_type: str
    travel_time: float
    blocked: bool
    hazard: bool
    cost: float = 0
    terrain_difficulty: float = 1.0
    capacity: float = 1.0
    available: bool = True
    flood_risk: float = 0.0
    evacuation_cost: float = 0.0

    def as_dict(self):
        return {
            "source": self.source,
            "destination": self.destination,
            "distance": self.distance,
            "elevation_change": self.elevation_change,
            "slope": self.slope,
            "surface_type": self.surface_type,
            "travel_time": self.travel_time,
            "blocked": self.blocked,
            "hazard": self.hazard,
            "cost": self.cost,
            "terrain_difficulty": self.terrain_difficulty,
            "capacity": self.capacity,
            "available": self.available,
            "flood_risk": self.flood_risk,
            "evacuation_cost": self.evacuation_cost,
        }


class Graph:
    def __init__(self):
        self.nodes = HashMap()
        self.adjacency = HashMap()

    def add_node(self, node: GraphNode):
        self.nodes[node.id] = node
        self.adjacency.setdefault(node.id, [])

    def add_edge(self, edge: GraphEdge):
        if edge.source not in self.nodes or edge.destination not in self.nodes:
            raise ValueError("Both edge nodes must exist in the graph")
        self.adjacency.setdefault(edge.source, []).append(edge)

    def neighbors(self, node_id):
        return self.adjacency.get(node_id, [])

    def node_count(self):
        return len(self.nodes)

    def edge_count(self):
        return sum(len(edges) for edges in self.adjacency.values())
