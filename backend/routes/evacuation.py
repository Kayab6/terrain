from __future__ import annotations

from time import perf_counter

from flask import current_app, jsonify, request

from algorithms.routing import dijkstra
from services.emergency import emergency_graph_summary, validate_scenario
from services.external_api import ExternalApiError
from services.route_graph import nearest_node
from services.elevation import load_elevations
from services.osm_features import load_map_features
from services.route_graph import build_graph_from_geojson

from . import api
from .errors import error_response


def _graph_for_scenario(payload):
    points = []
    for zone in payload["dangerZones"]:
        location = zone.get("location")
        if location is not None:
            points.append(location)
    for shelter in payload["shelters"]:
        points.append(shelter["location"])
    if not points:
        raise ValueError("At least one scenario location is required")
    west = min(point[0] for point in points) - 0.08
    east = max(point[0] for point in points) + 0.08
    south = min(point[1] for point in points) - 0.08
    north = max(point[1] for point in points) + 0.08
    features = load_map_features(south, west, north, east)
    unique_coordinates = []
    seen = set()
    for feature in features.get("features", []):
        for longitude, latitude in feature.get("geometry", {}).get("coordinates", []):
            key = (round(latitude, 6), round(longitude, 6))
            if key not in seen:
                seen.add(key)
                unique_coordinates.append(key)
    if not unique_coordinates:
        raise ValueError("No OSM roads or trails were available for evacuation routing")
    if len(unique_coordinates) > 200:
        raise ValueError("Selected area contains too many graph points")
    elevations = load_elevations([(latitude, longitude) for latitude, longitude in unique_coordinates])
    graph = build_graph_from_geojson(features, dict(zip(unique_coordinates, elevations)))
    return graph, points


def _apply_scenario(graph, payload):
    blocked_ids = set()
    for feature in payload.get("blockedRoads", []):
        blocked_ids.update(feature.get("edgeIds", []))
    for feature in payload.get("floodZones", []):
        if feature.get("edgeIds"):
            blocked_ids.update(feature["edgeIds"])
    for edges in graph.adjacency.values():
        for edge in edges:
            edge_id = f"{edge.source}-{edge.destination}"
            if edge_id in blocked_ids or edge_id in {str(value) for value in blocked_ids}:
                edge.blocked = True
                edge.available = False
            if edge.destination in blocked_ids:
                edge.blocked = True
            if edge.surface_type == "unknown":
                edge.terrain_difficulty = 1.5


@api.post("/api/evacuation/validate")
def validate_evacuation_scenario():
    payload = request.get_json(silent=True)
    errors, _ = validate_scenario(payload)
    return jsonify({
        "success": True,
        "valid": not errors,
        "invalidFeatures": errors,
        "disconnectedDangerZones": [],
        "inaccessibleShelters": [],
        "capacityShortfalls": [],
        "blockedCriticalLinks": [],
        "warnings": [] if not errors else ["Correct invalid scenario features before analysis"],
    }), 200 if not errors else 400


@api.post("/api/evacuation/preview")
def preview_evacuation_scenario():
    payload = request.get_json(silent=True)
    errors, _ = validate_scenario(payload)
    if errors:
        return error_response("; ".join(errors), 400, "invalid_request", errors)
    try:
        graph, points = _graph_for_scenario(payload)
        _apply_scenario(graph, payload)
    except ExternalApiError as exc:
        return error_response(str(exc), 502, "external_service_error")
    except ValueError as exc:
        return error_response(str(exc), 502, "invalid_osm_data")
    summary = emergency_graph_summary(graph)
    summary["candidateShelterAssignments"] = [
        {"shelterId": shelter["id"], "location": shelter["location"]}
        for shelter in payload["shelters"]
    ]
    summary["preliminaryBottlenecks"] = []
    return jsonify({"success": True, "preview": summary})


@api.post("/api/evacuation/analyze")
def analyze_evacuation_scenario():
    payload = request.get_json(silent=True)
    errors, _ = validate_scenario(payload)
    if errors:
        return error_response("; ".join(errors), 400, "invalid_request", errors)
    started = perf_counter()
    try:
        graph, _ = _graph_for_scenario(payload)
        _apply_scenario(graph, payload)
    except ExternalApiError as exc:
        return error_response(str(exc), 502, "external_service_error")
    except ValueError as exc:
        return error_response(str(exc), 502, "invalid_osm_data")

    assignments = []
    routes = []
    total_population = sum(float(zone["population"]) for zone in payload["dangerZones"])
    total_capacity = sum(float(shelter["capacity"]) for shelter in payload["shelters"])
    evacuated = 0.0
    shelter_remaining = [float(shelter["capacity"]) for shelter in payload["shelters"]]

    ranked_zones = sorted(
        payload["dangerZones"],
        key=lambda zone: ({"low": 1, "medium": 2, "high": 3, "critical": 4}[zone.get("severity", "medium")] * -1,
                          zone.get("priority", 1)),
    )
    for zone in ranked_zones:
        population = float(zone["population"])
        population_to_route = population
        zone_location = zone.get("location")
        if zone_location is None:
            continue
        try:
            source_node, _ = nearest_node(
                graph, float(zone_location[0]), float(zone_location[1]),
                current_app.config["ROUTE_MAX_DISTANCE_METERS"],
            )
        except ValueError as exc:
            return error_response(f"Danger zone {zone['id']} has no nearby route node: {exc}", 400, "nearest_node_not_found")

        candidates = []
        for shelter_index, shelter in enumerate(payload["shelters"]):
            try:
                shelter_node, _ = nearest_node(
                    graph, float(shelter["location"][0]), float(shelter["location"][1]),
                    current_app.config["ROUTE_MAX_DISTANCE_METERS"],
                )
            except ValueError:
                continue
            if shelter_remaining[shelter_index] <= 0:
                continue
            path, explored, _ = dijkstra(graph, source_node.id, shelter_node.id, payload["preference"])
            if path is not None:
                candidates.append((len(path), shelter_index, shelter_node, path, explored))
        if not candidates:
            continue
        _, shelter_index, shelter_node, path, explored = min(candidates, key=lambda candidate: candidate[0])
        allocated = min(population_to_route, shelter_remaining[shelter_index])
        shelter_remaining[shelter_index] -= allocated
        evacuated += allocated
        assignments.append({
            "dangerZoneId": zone["id"],
            "shelterId": payload["shelters"][shelter_index]["id"],
            "population": allocated,
        })
        coordinates = [
            [graph.nodes[node_id].longitude, graph.nodes[node_id].latitude]
            for node_id in path
        ]
        routes.append({
            "dangerZoneId": zone["id"],
            "shelterId": payload["shelters"][shelter_index]["id"],
            "population": allocated,
            "nodeIds": path,
            "nodesExplored": explored,
            "route": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {},
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                }],
            },
        })

    unmet = max(0.0, total_population - evacuated)
    graph_summary = emergency_graph_summary(graph)
    disconnected = graph_summary["reachableComponents"]
    if len(disconnected) > 1:
        disconnected_regions = [{"componentId": index, "nodeIds": component} for index, component in enumerate(disconnected)]
    else:
        disconnected_regions = []
    percentage = 100.0 if total_population == 0 else evacuated / total_population * 100
    warnings = []
    if unmet > 0:
        warnings.append(f"{unmet:g} people cannot be assigned to shelters")
    if not routes:
        warnings.append("No safe evacuation routes were found")

    return jsonify({
        "success": True,
        "summary": {
            "totalPopulation": total_population,
            "totalShelterCapacity": total_capacity,
            "evacuatedPopulation": evacuated,
            "unmetPopulation": unmet,
            "evacuationPercentage": round(percentage, 2),
        },
        "assignments": assignments,
        "routes": routes,
        "bottlenecks": [],
        "criticalMinCutEdges": [],
        "disconnectedRegions": disconnected_regions,
        "statistics": {
            "algorithm": payload["algorithm"],
            "executionTimeMs": round((perf_counter() - started) * 1000, 3),
        },
        "warnings": warnings,
    })
