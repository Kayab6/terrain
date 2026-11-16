from collections import deque


class DisjointSet:
    def __init__(self, nodes):
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}

    def find(self, node):
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, first, second):
        root_first = self.find(first)
        root_second = self.find(second)
        if root_first == root_second:
            return False
        if self.rank[root_first] < self.rank[root_second]:
            root_first, root_second = root_second, root_first
        self.parent[root_second] = root_first
        if self.rank[root_first] == self.rank[root_second]:
            self.rank[root_first] += 1
        return True


class Dinic:
    def __init__(self, node_count):
        self.graph = [[] for _ in range(node_count)]

    def add_edge(self, source, destination, capacity, original=None):
        forward = [destination, capacity, len(self.graph[destination]), original]
        reverse = [source, 0, len(self.graph[source]), original]
        self.graph[source].append(forward)
        self.graph[destination].append(reverse)
        return forward

    def max_flow(self, source, sink):
        flow = 0
        while True:
            level = [-1] * len(self.graph)
            level[source] = 0
            queue = deque([source])
            while queue:
                node = queue.popleft()
                for destination, capacity, _, _ in self.graph[node]:
                    if capacity > 0 and level[destination] < 0:
                        level[destination] = level[node] + 1
                        queue.append(destination)
            if level[sink] < 0:
                return flow

            positions = [0] * len(self.graph)

            def send(node, amount):
                if node == sink:
                    return amount
                while positions[node] < len(self.graph[node]):
                    edge = self.graph[node][positions[node]]
                    destination, capacity, reverse_index, original = edge
                    if capacity > 0 and level[destination] == level[node] + 1:
                        sent = send(destination, min(amount, capacity))
                        if sent:
                            edge[1] -= sent
                            self.graph[destination][reverse_index][1] += sent
                            return sent
                    positions[node] += 1
                return 0

            while True:
                sent = send(source, float("inf"))
                if sent == 0:
                    break
                flow += sent

    def min_cut_edges(self, source):
        reachable = {source}
        queue = deque([source])
        while queue:
            node = queue.popleft()
            for destination, capacity, _, original in self.graph[node]:
                if capacity > 0 and destination not in reachable:
                    reachable.add(destination)
                    queue.append(destination)
        result = []
        for node in reachable:
            for edge in self.graph[node]:
                destination, capacity, _, original = edge
                if destination not in reachable and original is not None and capacity >= 0:
                    result.append(original)
        return result
