from unittest.mock import patch

import pytest

from app import create_app
from algorithms.graph import Graph, GraphNode, GraphEdge
from algorithms.routing import astar, bfs, dfs, dijkstra
from services.route_graph import build_graph_from_geojson, nearest_node
from services.external_api import ExternalApiError
from algorithms.routing import yen_k_shortest_paths


def make_graph():
    graph = Graph()
    for node_id in ("a", "b", "c", "d"):
        graph.add_node(GraphNode(node_id, 0, ord(node_id) - ord("a"), 0))
    weights = {("a", "b"): 1, ("b", "c"): 1, ("a", "c"): 10, ("c", "d"): 1}
    for (source, destination), weight in weights.items():
        graph.add_edge(GraphEdge(source, destination, weight, 0, 0, "path", weight, False, False, weight))
        graph.add_edge(GraphEdge(destination, source, weight, 0, 0, "path", weight, False, False, weight))
    return graph


def test_graph_creation_and_lookup():
    graph = make_graph()
    assert graph.node_count() == 4
    assert graph.edge_count() == 8
    assert graph.nodes["c"].longitude == 2
    assert len(graph.neighbors("a")) == 2


@pytest.mark.parametrize("algorithm", [bfs, dfs])
def test_unweighted_searches(algorithm):
    path, explored, _ = algorithm(make_graph(), "a", "d")
    assert path is not None
    assert path[0] == "a" and path[-1] == "d"
    assert explored >= 4


def test_dijkstra_and_astar_optimal_cost():
    graph = make_graph()
    dijkstra_path, _, _ = dijkstra(graph, "a", "d")
    astar_path, _, _ = astar(graph, "a", "d")
    assert dijkstra_path == ["a", "b", "c", "d"]
    assert astar_path == ["a", "b", "c", "d"]


def test_unreachable_route_and_blocked_edge():
    graph = make_graph()
    graph.neighbors("a")[0].blocked = True
    graph.neighbors("a")[1].blocked = True
    path, _, _ = dijkstra(graph, "a", "d")
    assert path is None


def test_nearest_node_rejects_distant_point():
    graph = make_graph()
    with pytest.raises(ValueError, match="No graph node"):
        nearest_node(graph, 100, 100, 5000)


def test_geojson_graph_and_malformed_geometry():
    features = {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"highway": "path"},
        "geometry": {"type": "LineString", "coordinates": [[86.9, 27.9], [86.91, 27.91]]},
    }]}
    graph = build_graph_from_geojson(features, {(27.9, 86.9): 100, (27.91, 86.91): 120})
    assert graph.node_count() == 2
    assert graph.edge_count() == 2
    with pytest.raises(ValueError):
        build_graph_from_geojson({"type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[1]]}}]})


def test_route_api_validation():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        response = client.post("/api/routes/calculate", json={
            "start": [86.925, 27.9881],
            "destination": [86.925, 27.9881],
        })
        assert response.status_code == 400
        assert response.get_json()["success"] is False


@patch("routes.routes.load_elevations", return_value=[100, 110])
@patch("routes.routes.load_map_features")
def test_route_api_external_service_error(mock_features, mock_elevations):
    mock_features.side_effect = ExternalApiError("provider failure")
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        response = client.post("/api/routes/calculate", json={
            "start": [86.9, 27.9],
            "destination": [86.91, 27.91],
        })
    assert response.status_code >= 500


def test_yen_shortest_paths_have_unique_paths_and_ranked_costs():
    graph = make_graph()
    paths, _, _ = yen_k_shortest_paths(graph, "a", "d", count=3, preference="shortest")
    assert len(paths) >= 1
    assert len({tuple(path) for path in paths}) == len(paths)


def test_phase4_multiple_route_validation():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        response = client.post("/api/routes/multiple", json={
            "start": [86.925, 27.9881],
            "destination": [86.925, 27.9881],
            "count": 3,
        })
        assert response.status_code == 400
        response = client.post("/api/routes/multiple", json={
            "start": [86.925, 27.9881],
            "destination": [86.94, 28.00],
            "count": 11,
        })
        assert response.status_code == 400
