import itertools
import time

from flask import current_app, jsonify, request

from algorithms.routing import astar, bfs, dfs, dijkstra, yen_k_shortest_paths
from services.osm_features import load_map_features
from services.external_api import ExternalApiError
from services.elevation import load_elevations
from services.route_graph import build_graph_from_geojson, nearest_node

from . import api
from .errors import error_response


ALGORITHMS = {"bfs": bfs, "dfs": dfs, "dijkstra": dijkstra, "astar": astar}
PREFERENCES = {"shortest", "fastest", "easiest", "lowest_elevation", "safest"}


def _route_metrics(graph, path):
    edges = []
    for source, destination in zip(path, path[1:]):
        edge = next(
            (
                candidate
                for candidate in graph.neighbors(source)
                if candidate.destination == destination
            ),
            None,
        )
        if edge is None:
            raise ValueError("Route path contains disconnected graph nodes")
        edges.append(edge)

    distance = sum(edge.distance for edge in edges)
    travel_time = sum(edge.travel_time for edge in edges)
    elevation_gain = sum(max(0, edge.elevation_change) for edge in edges)
    elevation_loss = sum(max(0, -edge.elevation_change) for edge in edges)
    maximum_slope = max((edge.slope for edge in edges), default=0)
    difficulty = sum(
        (edge.slope / 100) + (1.5 if edge.hazard else 0) for edge in edges
    )
    difficulty = min(10, max(0, difficulty / max(len(edges), 1) * 10))
    return {
        "distance": distance,
        "estimated_time": travel_time,
        "elevation_gain": elevation_gain,
        "elevation_loss": elevation_loss,
        "maximum_slope": maximum_slope,
        "terrain_difficulty": round(difficulty, 2),
        "safety_score": round(max(0, 100 - sum(20 if edge.hazard else 0 for edge in edges) / max(len(edges), 1)), 1),
    }


def _validate_coordinates(coordinates):
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        return None
    try:
        longitude, latitude = map(float, coordinates)
    except (TypeError, ValueError):
        return None
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        return None
    return longitude, latitude


def _load_route_graph(points):
    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]
    west, east = min(longitudes) - 0.08, max(longitudes) + 0.08
    south, north = min(latitudes) - 0.08, max(latitudes) + 0.08
    features = load_map_features(south, west, north, east)
    unique_coordinates = []
    seen_coordinates = set()
    for feature in features.get("features", []):
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        for longitude, latitude in coordinates:
            key = (round(latitude, 6), round(longitude, 6))
            if key not in seen_coordinates:
                seen_coordinates.add(key)
                unique_coordinates.append(key)
    if not unique_coordinates:
        raise ValueError("No OSM roads or trails were available for routing")
    if len(unique_coordinates) > 200:
        raise ValueError("Selected area contains too many graph points for elevation lookup")
    elevations = load_elevations([(latitude, longitude) for latitude, longitude in unique_coordinates])
    graph = build_graph_from_geojson(
        features,
        dict(zip(unique_coordinates, elevations)),
    )
    return graph


def _line_for_path(graph, path):
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [graph.nodes[node_id].longitude, graph.nodes[node_id].latitude]
                    for node_id in path
                ],
            },
        }],
    }


@api.post("/api/routes/calculate")
def calculate_route():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON object", 400, "invalid_request")

    start = payload.get("start")
    destination = payload.get("destination")
    stops = payload.get("stops", [])
    algorithm = payload.get("algorithm", "dijkstra").lower()
    preference = payload.get("preference", "shortest")
    if not isinstance(start, list) or len(start) != 2 or not isinstance(destination, list) or len(destination) != 2:
        return error_response("start and destination must be [longitude, latitude]", 400, "invalid_coordinates")
    try:
        start_lng, start_lat = map(float, start)
        destination_lng, destination_lat = map(float, destination)
    except (TypeError, ValueError):
        return error_response("Coordinates must be numeric", 400, "invalid_coordinates")
    if not isinstance(stops, list):
        return error_response("stops must be an array of [longitude, latitude]", 400, "invalid_coordinates")
    validated_stops = []
    for stop in stops:
        validated_stop = _validate_coordinates(stop)
        if validated_stop is None:
            return error_response("Every checkpoint must contain valid longitude and latitude", 400, "invalid_coordinates")
        validated_stops.append(validated_stop)
    if not -180 <= start_lng <= 180 or not -90 <= start_lat <= 90 or not -180 <= destination_lng <= 180 or not -90 <= destination_lat <= 90:
        return error_response("Coordinates are outside valid longitude/latitude ranges", 400, "invalid_coordinates")
    if abs(start_lng - destination_lng) < 1e-7 and abs(start_lat - destination_lat) < 1e-7:
        return error_response("Start and destination cannot be identical", 400, "invalid_coordinates")
    if any(
        abs(stop[0] - start_lng) < 1e-7 and abs(stop[1] - start_lat) < 1e-7
        or abs(stop[0] - destination_lng) < 1e-7 and abs(stop[1] - destination_lat) < 1e-7
        for stop in validated_stops
    ):
        return error_response("Checkpoints cannot duplicate Start or Destination", 400, "invalid_coordinates")
    if len({(round(stop[0], 7), round(stop[1], 7)) for stop in validated_stops}) != len(validated_stops):
        return error_response("Checkpoints cannot duplicate another checkpoint", 400, "invalid_coordinates")
    if algorithm not in ALGORITHMS:
        return error_response("Unsupported routing algorithm", 400, "invalid_request")
    if preference not in PREFERENCES:
        return error_response("Unsupported route preference", 400, "invalid_request")

    ordered_points = [(start_lng, start_lat), *validated_stops, (destination_lng, destination_lat)]
    west = min(point[0] for point in ordered_points) - 0.08
    east = max(point[0] for point in ordered_points) + 0.08
    south = min(point[1] for point in ordered_points) - 0.08
    north = max(point[1] for point in ordered_points) + 0.08
    try:
        features = load_map_features(south, west, north, east)
        unique_coordinates = []
        seen_coordinates = set()
        for feature in features.get("features", []):
            for longitude, latitude in feature.get("geometry", {}).get("coordinates", []):
                key = (round(latitude, 6), round(longitude, 6))
                if key not in seen_coordinates:
                    seen_coordinates.add(key)
                    unique_coordinates.append(key)
        if len(unique_coordinates) > 200:
            return error_response(
                "Selected area contains too many graph points for elevation lookup (maximum 200)",
                413,
                "area_too_large",
            )
        elevations = load_elevations([(latitude, longitude) for latitude, longitude in unique_coordinates])
        elevations_by_coordinate = dict(zip(unique_coordinates, elevations))
        graph = build_graph_from_geojson(features, elevations_by_coordinate)
    except ExternalApiError as exc:
        return error_response(str(exc), 502, "external_service_error")
    except ValueError as exc:
        return error_response(str(exc), 502, "invalid_osm_data")

    try:
        mapped_nodes = [
            nearest_node(graph, longitude, latitude, current_app.config["ROUTE_MAX_DISTANCE_METERS"])[0]
            for longitude, latitude in ordered_points
        ]
    except ValueError as exc:
        return error_response(str(exc), 400, "nearest_node_not_found")

    started = time.perf_counter()
    paths = []
    total_explored = 0
    total_algorithm_time = 0
    for source_node, destination_node in zip(mapped_nodes, mapped_nodes[1:]):
        segment_path, explored, algorithm_time = ALGORITHMS[algorithm](
            graph, source_node.id, destination_node.id, preference
        )
        if segment_path is None:
            return error_response("No route exists between a selected route point and the next point", 404, "route_not_found")
        paths.append(segment_path)
        total_explored += explored
        total_algorithm_time += algorithm_time or 0
    total_time = (time.perf_counter() - started) * 1000
    combined_path = []
    segment_metrics = []
    for path in paths:
        combined_path.extend(path if not combined_path else path[1:])
        segment_metrics.append(_route_metrics(graph, path))
    metrics = {
        key: sum(float(segment[key]) for segment in segment_metrics)
        for key in ("distance", "estimated_time", "elevation_gain", "elevation_loss")
    }
    metrics.update({
        "maximum_slope": max((segment["maximum_slope"] for segment in segment_metrics), default=0),
        "terrain_difficulty": round(sum(segment["terrain_difficulty"] for segment in segment_metrics) / max(len(segment_metrics), 1), 2),
        "safety_score": round(sum(segment["safety_score"] for segment in segment_metrics) / max(len(segment_metrics), 1), 1),
    })
    coordinates = [[graph.nodes[node_id].longitude, graph.nodes[node_id].latitude] for node_id in combined_path]
    return jsonify({
        "success": True,
        "data": {
            "route": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {},
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                }],
            },
            "node_ids": combined_path,
            "algorithm": algorithm,
            "preference": preference,
            "nodes_explored": total_explored,
            "execution_time": round(total_algorithm_time or total_time, 3),
            **metrics,
        },
    })


@api.post("/api/routes/multiple")
def calculate_multiple_routes():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON object", 400, "invalid_request")
    start = _validate_coordinates(payload.get("start"))
    destination = _validate_coordinates(payload.get("destination"))
    if start is None or destination is None:
        return error_response("Coordinates must contain valid longitude and latitude", 400, "invalid_coordinates")
    if start == destination:
        return error_response("Start and destination cannot be identical", 400, "invalid_coordinates")
    algorithm = str(payload.get("algorithm", "astar")).lower()
    preference = str(payload.get("preference", "shortest"))
    count = payload.get("count", 3)
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 10:
        return error_response("count must be an integer from 1 to 10", 400, "invalid_request")
    if algorithm not in ALGORITHMS:
        return error_response("Unsupported routing algorithm", 400, "invalid_request")
    if preference not in PREFERENCES:
        return error_response("Unsupported route preference", 400, "invalid_request")
    try:
        graph = _load_route_graph([start, destination])
    except ExternalApiError as exc:
        return error_response(str(exc), 502, "external_service_error")
    except ValueError as exc:
        return error_response(str(exc), 502, "invalid_osm_data")
    try:
        start_node, _ = nearest_node(graph, start[0], start[1], current_app.config["ROUTE_MAX_DISTANCE_METERS"])
        destination_node, _ = nearest_node(graph, destination[0], destination[1], current_app.config["ROUTE_MAX_DISTANCE_METERS"])
    except ValueError as exc:
        return error_response(str(exc), 400, "nearest_node_not_found")

    paths, explored, execution_time = yen_k_shortest_paths(
        graph, start_node.id, destination_node.id, count, preference
    )
    if not paths:
        return error_response("No route exists between the selected points", 404, "route_not_found")
    alternatives = []
    for rank, path in enumerate(paths, start=1):
        metrics = _route_metrics(graph, path)
        alternatives.append({
            "route": _line_for_path(graph, path),
            "node_ids": path,
            "rank": rank,
            "recommended": rank == 1,
            "nodes_explored": explored,
            "execution_time": round(execution_time, 3),
            **metrics,
        })
    return jsonify({"success": True, "data": {"routes": alternatives}})


MULTI_STOP_PREFERENCES = {
    "shortest_total_distance": "shortest",
    "fastest_total_time": "fastest",
    "lowest_total_elevation": "lowest_elevation",
    "safest_total_route": "safest",
}


@api.post("/api/routes/multi-stop")
def calculate_multi_stop_route():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON object", 400, "invalid_request")
    start = _validate_coordinates(payload.get("start"))
    destination = _validate_coordinates(payload.get("destination"))
    stops = payload.get("stops", [])
    if start is None or destination is None or not isinstance(stops, list):
        return error_response("start, destination, and stops must contain valid coordinates", 400, "invalid_coordinates")
    validated_stops = [_validate_coordinates(stop) for stop in stops]
    if any(stop is None for stop in validated_stops):
        return error_response("Every checkpoint must contain valid longitude and latitude", 400, "invalid_coordinates")
    if start == destination:
        return error_response("Start and destination cannot be identical", 400, "invalid_coordinates")
    preference = str(payload.get("preference", "shortest_total_distance"))
    strategy = str(payload.get("strategy", "auto")).lower()
    if preference not in MULTI_STOP_PREFERENCES:
        return error_response("Unsupported multi-stop preference", 400, "invalid_request")
    if strategy not in {"auto", "exact", "greedy"}:
        return error_response("Unsupported multi-stop strategy", 400, "invalid_request")

    try:
        graph = _load_route_graph([start, *validated_stops, destination])
    except ExternalApiError as exc:
        return error_response(str(exc), 502, "external_service_error")
    except ValueError as exc:
        return error_response(str(exc), 502, "invalid_osm_data")
    points = [start, *validated_stops, destination]
    mapped_nodes = []
    for coordinate in points:
        try:
            node, _ = nearest_node(graph, coordinate[0], coordinate[1], current_app.config["ROUTE_MAX_DISTANCE_METERS"])
            mapped_nodes.append(node)
        except ValueError as exc:
            return error_response(f"Checkpoint {coordinate} is unreachable: {exc}", 400, "nearest_node_not_found")

    if len(validated_stops) + 1 <= current_app.config["MULTI_STOP_EXACT_THRESHOLD"] and strategy != "greedy":
        used_strategy = "exact"
    else:
        used_strategy = "greedy"
    path_preference = MULTI_STOP_PREFERENCES[preference]

    stop_indexes = list(range(1, len(points) - 1))
    orders = [tuple(stop_indexes)] if not stop_indexes else None
    evaluated = 0
    if used_strategy == "exact" and stop_indexes:
        orders = []
        for permutation in itertools.permutations(stop_indexes):
            evaluated += 1
            orders.append(permutation)
    elif used_strategy == "greedy" and stop_indexes:
        remaining = set(stop_indexes)
        current = 0
        order = []
        current_node = mapped_nodes[0]
        while remaining:
            choices = []
            for index in remaining:
                path, _, _ = dijkstra(graph, current_node.id, mapped_nodes[index].id, path_preference)
                if path is not None:
                    choices.append((_route_segment_cost(graph, path, path_preference), index, path))
            if not choices:
                return error_response("A checkpoint is unreachable", 404, "checkpoint_unreachable")
            _, index, _ = min(choices, key=lambda choice: choice[:2])
            order.append(index)
            remaining.remove(index)
            current_node = mapped_nodes[index]
            evaluated += 1
        orders = [tuple(order)]

    best_order = None
    best_cost = float("inf")
    segment_cache = {}
    for order in orders or [tuple()]:
        sequence = (0, *order, len(points) - 1)
        total_cost = 0
        reachable = True
        for source_index, destination_index in zip(sequence, sequence[1:]):
            key = (mapped_nodes[source_index].id, mapped_nodes[destination_index].id)
            if key not in segment_cache:
                segment_cache[key] = dijkstra(
                    graph, key[0], key[1], path_preference
                )[0]
            segment = segment_cache[key]
            if segment is None:
                reachable = False
                break
            total_cost += _route_segment_cost(graph, segment, path_preference)
        if reachable and total_cost < best_cost:
            best_cost = total_cost
            best_order = order

    if best_order is None:
        return error_response("One or more checkpoints are unreachable", 404, "checkpoint_unreachable")
    sequence = (0, *best_order, len(points) - 1)
    combined_nodes = []
    segments = []
    for source_index, destination_index in zip(sequence, sequence[1:]):
        source_node = mapped_nodes[source_index]
        destination_node = mapped_nodes[destination_index]
        path = dijkstra(graph, source_node.id, destination_node.id, path_preference)[0]
        if path is None:
            return error_response("One or more checkpoints are unreachable", 404, "checkpoint_unreachable")
        combined_nodes.extend(path if not combined_nodes else path[1:])
        metrics = _route_metrics(graph, path)
        segments.append({"from": source_index, "to": destination_index, "node_ids": path, "route": _line_for_path(graph, path), **metrics})

    combined_metrics = {
        "total_distance": sum(segment["distance"] for segment in segments),
        "total_travel_time": sum(segment["estimated_time"] for segment in segments),
        "total_elevation_gain": sum(segment["elevation_gain"] for segment in segments),
        "total_elevation_loss": sum(segment["elevation_loss"] for segment in segments),
        "maximum_slope": max((segment["maximum_slope"] for segment in segments), default=0),
        "overall_difficulty": round(sum(segment["terrain_difficulty"] for segment in segments) / max(len(segments), 1), 2),
    }
    optimized_order = [stop_indexes[index - 1] if index else index for index in best_order]
    optimized_coordinates = [points[index] for index in (0, *best_order, len(points) - 1)]
    return jsonify({
        "success": True,
        "data": {
            "optimized_stop_order": optimized_coordinates[1:-1],
            "optimized_stop_indices": list(best_order),
            "segment_routes": segments,
            "route": _line_for_path(graph, combined_nodes),
            "optimization_strategy": used_strategy,
            "states_evaluated": evaluated,
            **combined_metrics,
        },
    })


def _route_segment_cost(graph, path, preference):
    return sum(
        __import__("services.route_graph", fromlist=["calculate_edge_cost"]).calculate_edge_cost(edge, preference)
        for source, destination in zip(path, path[1:])
        for edge in graph.neighbors(source)
        if edge.destination == destination and not edge.blocked
    )
