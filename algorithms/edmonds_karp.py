from collections import deque

def bfs(capacity, flow, s, t):
    parent = {node: None for node in capacity}
    parent[s] = s
    q = deque([s])

    while q:
        u = q.popleft()
        for v in capacity[u]:
            if parent[v] is None and capacity[u][v] - flow[u][v] > 0:
                parent[v] = u
                if v == t:
                    return parent
                q.append(v)
    return None


def edmonds_karp(capacity, s, t):
    flow = {u: {v: 0 for v in capacity[u]} for u in capacity}
    max_flow = 0

    while True:
        parent = bfs(capacity, flow, s, t)
        if not parent:
            break

        # encontrar bottleneck
        v = t
        bottleneck = float("inf")
        while v != s:
            u = parent[v]
            bottleneck = min(bottleneck, capacity[u][v] - flow[u][v])
            v = u

        # aumentar flujo
        v = t
        while v != s:
            u = parent[v]
            flow[u][v] += bottleneck
            flow[v][u] -= bottleneck
            v = u

        max_flow += bottleneck

    return max_flow
