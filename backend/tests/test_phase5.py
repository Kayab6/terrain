from app import create_app
from algorithms.emergency import Dinic, DisjointSet
from algorithms.graph import Graph, GraphEdge, GraphNode
from services.emergency import emergency_graph_summary, validate_scenario


def test_disjoint_set_connectivity():
    disjoint = DisjointSet(["a", "b", "c"])
    assert disjoint.union("a", "b")
    assert disjoint.find("a") == disjoint.find("b")
    assert disjoint.find("a") != disjoint.find("c")


def test_dinic_max_flow_and_cut():
    flow = Dinic(4)
    flow.add_edge(0, 1, 10, "road-a")
    flow.add_edge(1, 2, 4, "road-b")
    flow.add_edge(1, 3, 6, "road-c")
    flow.add_edge(2, 3, 10, "road-d")
    assert flow.max_flow(0, 3) == 10
    assert isinstance(flow.min_cut_edges(0), list)


def valid_payload():
    return {
        "dangerZones": [{
            "id": "zone-1",
            "location": [-73.9, 40.7],
            "population": 500,
            "severity": "high",
            "priority": 1,
        }],
        "shelters": [{
            "id": "shelter-1",
            "location": [-73.8, 40.75],
            "capacity": 800,
        }],
        "blockedRoads": [],
        "floodZones": [],
        "preference": "safest",
        "algorithm": "max_flow",
    }


def test_valid_scenario():
    errors, scenario = validate_scenario(valid_payload())
    assert errors == []
    assert scenario.preference == "safest"


def test_empty_scenario_and_duplicate_ids():
    errors, _ = validate_scenario({"dangerZones": [], "shelters": []})
    assert errors
    payload = valid_payload()
    payload["shelters"][0]["id"] = "zone-1"
    errors, _ = validate_scenario(payload)
    assert any("unique" in error.lower() for error in errors)


def test_invalid_polygon_and_negative_capacity():
    payload = valid_payload()
    payload["dangerZones"][0]["location"] = None
    payload["dangerZones"][0]["geometry"] = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [0, 0]]],
    }
    payload["shelters"][0]["capacity"] = -1
    errors, _ = validate_scenario(payload)
    assert errors


def test_emergency_graph_summary_detects_blocked_and_flooded_edges():
    graph = Graph()
    graph.add_node(GraphNode("a", 0, 0, 0))
    graph.add_node(GraphNode("b", 0, 1, 0))
    graph.add_edge(GraphEdge("a", "b", 100, 0, 0, "path", 100, True, False, capacity=1))
    graph.add_edge(GraphEdge("b", "a", 100, 0, 0, "path", 100, False, False, capacity=1, flood_risk=0.7))
    summary = emergency_graph_summary(graph)
    assert summary["blockedEdgeCount"] >= 1
    assert summary["floodAffectedEdgeCount"] >= 1


def test_evacuation_validation_api():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        response = client.post("/api/evacuation/validate", json=valid_payload())
        assert response.status_code == 200
        assert response.get_json()["valid"] is True

        invalid = client.post("/api/evacuation/validate", json={"dangerZones": [], "shelters": []})
        assert invalid.status_code == 400
        assert invalid.get_json()["success"] is True
