def bellman_ford(graph, start, end):
    # Convertir en lista de aristas
    edges = []
    for node in graph:
        for neigh, w in graph[node]:
            edges.append((node, neigh, w))

    # Inicialización
    dist = {node: float("inf") for node in graph}
    dist[start] = 0
    parent = {node: None for node in graph}

    V = len(graph)

    # Relaxar V-1 veces
    for _ in range(V - 1):
        changed = False
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                parent[v] = u
                changed = True
        if not changed:
            break

    # Reconstrucción de ruta
    route = []
    curr = end
    while curr is not None:
        route.append(curr)
        curr = parent[curr]

    return dist[end], list(reversed(route))
