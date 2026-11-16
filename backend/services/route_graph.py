from __future__ import annotations

from math import isfinite, radians, sin, cos, asin, sqrt

from algorithms.graph import Graph, GraphEdge, GraphNode, haversine_meters


SURFACE_DIFFICULTY = {
    "path": 1.2,
    "track": 1.35,
    "footway": 1.15,
    "bridleway": 1.3,
    "steps": 1.8,
    "service": 1.0,
    "residential": 1.05,
    "unclassified": 1.1,
    "primary": 1.15,
    "secondary": 1.25,
    "tertiary": 1.3,
}


def haversine_km(lng1, lat1, lng2, lat2):
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    delta_lat = lat2 - lat1
    delta_lng = lng2 - lng1
    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


def nearest_node(graph, longitude, latitude, max_distance_meters):
    target = (latitude, longitude)
    nearest = None
    nearest_distance = float("inf")
    for node in graph.nodes.values():
        distance = haversine_meters(target, (node.latitude, node.longitude))
        if distance < nearest_distance:
            nearest = node
            nearest_distance = distance
    if nearest is None or nearest_distance > max_distance_meters:
        raise ValueError(
            f"No graph node found within {max_distance_meters:.0f} meters"
        )
    return nearest, nearest_distance


def calculate_edge_cost(edge, preference="shortest", model=None):
    if edge.blocked:
        return float("inf")

    model = model or {}
    distance_weight = float(model.get("distance_weight", 1.0))
    elevation_weight = float(model.get("elevation_gain_weight", 1.5))
    slope_weight = float(model.get("slope_weight", 2.0))
    surface_weight = float(model.get("surface_weight", 0.6))
    hazard_weight = float(model.get("hazard_weight", 8.0))

    if preference == "fastest":
        return edge.travel_time * distance_weight
    if preference == "easiest":
        return (
            edge.distance * distance_weight
            + max(edge.slope, 0) * slope_weight
            + edge.distance / 1000 * surface_weight
            + hazard_weight * edge.hazard
        )
    if preference == "lowest_elevation":
        return (
            edge.distance * distance_weight
            + max(edge.elevation_change, 0) * elevation_weight
            + max(edge.slope, 0) * slope_weight
        )
    if preference == "safest":
        return (
            edge.distance * distance_weight
            + hazard_weight * edge.hazard
            + 20 * float(edge.blocked)
        )
    return edge.distance * distance_weight + max(edge.elevation_change, 0) * elevation_weight


def build_graph_from_geojson(feature_collection, elevation_by_coordinate=None):
    elevation_by_coordinate = elevation_by_coordinate or {}
    graph = Graph()
    node_by_coordinate = {}

    def add_node(longitude, latitude):
        key = (round(latitude, 7), round(longitude, 7))
        if key not in node_by_coordinate:
            node_id = f"node-{len(node_by_coordinate)}"
            elevation = float(elevation_by_coordinate.get(key, 0.0))
            graph.add_node(GraphNode(node_id, latitude, longitude, elevation, {"osm": True}))
            node_by_coordinate[key] = node_id
        return node_by_coordinate[key]

    if not isinstance(feature_collection, dict):
        raise ValueError("OSM GeoJSON must be an object")
    for feature in feature_collection.get("features", []):
        if not isinstance(feature, dict) or not isinstance(feature.get("geometry"), dict):
            raise ValueError("Malformed OSM feature geometry")
        geometry = feature["geometry"]
        if geometry.get("type") != "LineString":
            continue
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise ValueError("Malformed OSM LineString geometry")
        properties = feature.get("properties") or {}
        surface = str(properties.get("surface") or properties.get("highway") or "unknown")
        blocked = str(properties.get("access") or "").lower() in {"no", "private"}
        hazard = "hazard" in properties
        node_ids = []
        for coordinate in coordinates:
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ValueError("Malformed OSM coordinate")
            longitude, latitude = coordinate
            if isinstance(longitude, bool) or isinstance(latitude, bool):
                raise ValueError("Malformed OSM coordinate")
            try:
                longitude = float(longitude)
                latitude = float(latitude)
            except (TypeError, ValueError) as exc:
                raise ValueError("Malformed OSM coordinate") from exc
            if not isfinite(longitude) or not isfinite(latitude):
                raise ValueError("Malformed OSM coordinate")
            node_ids.append(add_node(longitude, latitude))

        for source_id, destination_id in zip(node_ids, node_ids[1:]):
            source = graph.nodes[source_id]
            destination = graph.nodes[destination_id]
            distance = haversine_meters(
                (source.latitude, source.longitude),
                (destination.latitude, destination.longitude),
            )
            elevation_change = destination.elevation - source.elevation
            slope = abs(elevation_change) / distance * 100 if distance else 0
            speed_kmh = 4.5 if surface in {"footway", "path", "track", "steps"} else 5.5
            travel_time = distance / 1000 / speed_kmh * 3600
            edge = GraphEdge(
                source_id,
                destination_id,
                distance,
                elevation_change,
                slope,
                surface,
                travel_time,
                blocked,
                hazard,
            )
            edge.cost = calculate_edge_cost(edge)
            graph.add_edge(edge)
            reverse = GraphEdge(
                destination_id,
                source_id,
                distance,
                -elevation_change,
                slope,
                surface,
                travel_time,
                blocked,
                hazard,
            )
            reverse.cost = calculate_edge_cost(reverse)
            graph.add_edge(reverse)
    return graph
