import heapq

def dijkstra(graph, start, end):
    """
    graph: dict { node: [(neighbor, weight), ...] }
    start: string ID
    end: string ID
    """

    pq = []
    heapq.heappush(pq, (0, start))
    distances = {node: float("inf") for node in graph}
    distances[start] = 0
    parent = {node: None for node in graph}

    while pq:
        dist, node = heapq.heappop(pq)

        if node == end:
            break

        if dist > distances[node]:
            continue

        for neighbor, weight in graph[node]:
            new_cost = dist + weight

            if new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                parent[neighbor] = node
                heapq.heappush(pq, (new_cost, neighbor))

    # Reconstruir ruta
    route = []
    curr = end
    while curr is not None:
        route.append(curr)
        curr = parent[curr]

    return distances[end], list(reversed(route))
