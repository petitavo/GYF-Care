import numpy as np

def floyd_warshall(graph):
    nodes = list(graph.keys())
    index = {nodes[i]: i for i in range(len(nodes))}
    n = len(nodes)

    dist = np.full((n, n), float("inf"))
    next_hop = [[None] * n for _ in range(n)]

    # Inicialización
    for u in nodes:
        dist[index[u]][index[u]] = 0
        for v, w in graph[u]:
            dist[index[u]][index[v]] = w
            next_hop[index[u]][index[v]] = v

    # DP
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_hop[i][j] = next_hop[i][k]

    return nodes, dist, next_hop


def get_fw_path(start, end, nodes, next_hop):
    idx = {nodes[i]: i for i in range(len(nodes))}
    i, j = idx[start], idx[end]

    if next_hop[i][j] is None:
        return None

    path = [start]
    while start != end:
        start = next_hop[idx[start]][j]
        path.append(start)
    return path
