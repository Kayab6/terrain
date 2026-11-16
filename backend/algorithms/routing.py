from __future__ import annotations

import itertools
import math
import time

from services.route_graph import calculate_edge_cost

from .data_structures import HashSet, MinHeap, Queue, Stack


def reconstruct_path(parents, destination):
    if destination not in parents:
        return None
    path = [destination]
    while parents[path[-1]] is not None:
        path.append(parents[path[-1]])
    return list(reversed(path))


def bfs(graph, start, destination, preference="shortest"):
    del preference
    started = time.perf_counter()
    queue = Queue([start])
    visited = HashSet([start])
    parents = {start: None}
    while queue:
        node_id = queue.dequeue()
        if node_id == destination:
            return reconstruct_path(parents, destination), len(visited), (time.perf_counter() - started) * 1000
        for edge in graph.neighbors(node_id):
            if edge.blocked or edge.destination in visited:
                continue
            visited.add(edge.destination)
            parents[edge.destination] = node_id
            queue.enqueue(edge.destination)
    return None, len(visited), (time.perf_counter() - started) * 1000


def dfs(graph, start, destination, preference="shortest"):
    del preference
    started = time.perf_counter()
    stack = Stack([start])
    visited = HashSet([start])
    parents = {start: None}
    while stack:
        node_id = stack.pop()
        if node_id == destination:
            return reconstruct_path(parents, destination), len(visited), (time.perf_counter() - started) * 1000
        for edge in reversed(graph.neighbors(node_id)):
            if edge.blocked or edge.destination in visited:
                continue
            visited.add(edge.destination)
            parents[edge.destination] = node_id
            stack.push(edge.destination)
    return None, len(visited), (time.perf_counter() - started) * 1000


def _weighted_search(graph, start, destination, preference, astar=False):
    started = time.perf_counter()
    counter = itertools.count()
    heap = MinHeap()
    heap.push(0, (start, 0))
    costs = {start: 0}
    parents = {start: None}
    visited = HashSet()

    while heap:
        _, (node_id, _) = heap.pop()
        if node_id in visited:
            continue
        visited.add(node_id)
        if node_id == destination:
            return reconstruct_path(parents, destination), len(visited), (time.perf_counter() - started) * 1000
        node = graph.nodes[node_id]
        destination_node = graph.nodes[destination]
        for edge in graph.neighbors(node_id):
            if edge.blocked:
                continue
            edge_cost = calculate_edge_cost(edge, preference)
            if not math.isfinite(edge_cost):
                continue
            new_cost = costs[node_id] + edge_cost
            if new_cost >= costs.get(edge.destination, math.inf):
                continue
            costs[edge.destination] = new_cost
            parents[edge.destination] = node_id
            heuristic = 0
            if astar:
                target = graph.nodes[edge.destination]
                heuristic = haversine_meters(
                    (target.latitude, target.longitude),
                    (destination_node.latitude, destination_node.longitude),
                ) / 1000000
            heap.push(new_cost + heuristic, (edge.destination, next(counter)))
    return None, len(visited), (time.perf_counter() - started) * 1000


def haversine_meters(first, second):
    lat1 = math.radians(first[0])
    lon1 = math.radians(first[1])
    lat2 = math.radians(second[0])
    lon2 = math.radians(second[1])
    lat_delta = lat2 - lat1
    lon_delta = lon2 - lon1
    a = math.sin(lat_delta / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(lon_delta / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(a))


def dijkstra(graph, start, destination, preference="shortest"):
    return _weighted_search(graph, start, destination, preference, astar=False)


def astar(graph, start, destination, preference="shortest"):
    return _weighted_search(graph, start, destination, preference, astar=True)


def path_cost(graph, path, preference="shortest"):
    total = 0
    for source, destination in zip(path, path[1:]):
        edge = next(
            (candidate for candidate in graph.neighbors(source)
             if candidate.destination == destination and not candidate.blocked),
            None,
        )
        if edge is None:
            return math.inf
        total += calculate_edge_cost(edge, preference)
    return total


def shortest_path_with_exclusions(graph, start, destination, preference="shortest",
                                  excluded_nodes=None, excluded_edges=None):
    excluded_nodes = excluded_nodes or set()
    excluded_edges = excluded_edges or set()
    counter = itertools.count()
    heap = MinHeap()
    heap.push(0, (start, next(counter)))
    costs = {start: 0}
    parents = {start: None}
    while heap:
        _, (node_id, _) = heap.pop()
        if node_id == destination:
            return reconstruct_path(parents, destination)
        if node_id in excluded_nodes:
            continue
        for edge in graph.neighbors(node_id):
            pair = (edge.source, edge.destination)
            if edge.blocked or pair in excluded_edges or edge.destination in excluded_nodes:
                continue
            new_cost = costs[node_id] + calculate_edge_cost(edge, preference)
            if new_cost < costs.get(edge.destination, math.inf):
                costs[edge.destination] = new_cost
                parents[edge.destination] = node_id
                heap.push(new_cost, (edge.destination, next(counter)))
    return None


def yen_k_shortest_paths(graph, start, destination, count=3, preference="shortest"):
    started = time.perf_counter()
    first = shortest_path_with_exclusions(graph, start, destination, preference)
    if first is None:
        return [], 0, (time.perf_counter() - started) * 1000

    accepted = [first]
    candidates = []
    candidate_keys = set()
    for route_rank in range(1, count):
        previous = accepted[route_rank - 1]
        for spur_index in range(len(previous) - 1):
            root_path = previous[:spur_index + 1]
            spur_node = previous[spur_index]
            excluded_nodes = set(root_path[:-1])
            excluded_edges = set()
            for accepted_path in accepted:
                if accepted_path[:spur_index + 1] == root_path:
                    excluded_edges.add((accepted_path[spur_index], accepted_path[spur_index + 1]))
            spur_path = shortest_path_with_exclusions(
                graph, spur_node, destination, preference,
                excluded_nodes=excluded_nodes, excluded_edges=excluded_edges,
            )
            if spur_path is None:
                continue
            complete = root_path[:-1] + spur_path
            complete_tuple = tuple(complete)
            if complete_tuple in candidate_keys or complete in accepted:
                continue
            candidate_keys.add(complete_tuple)
            candidates.append((path_cost(graph, complete, preference), complete))

        if not candidates:
            break
        candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
        _, best = candidates.pop(0)
        accepted.append(best)

    return accepted, sum(1 for node in graph.nodes if node), (time.perf_counter() - started) * 1000
