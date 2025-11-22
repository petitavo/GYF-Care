def kruskal(graph):
    edges = []
    for u in graph:
        for v, w in graph[u]:
            edges.append((w, u, v))

    parent = {}
    rank = {}

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] > rank[ry]:
            parent[ry] = rx
        elif rank[rx] < rank[ry]:
            parent[rx] = ry
        else:
            parent[ry] = rx
            rank[rx] += 1
        return True

    for node in graph:
        parent[node] = node
        rank[node] = 0

    mst = []
    cost = 0

    for w, u, v in sorted(edges):
        if union(u, v):
            mst.append((u, v, w))
            cost += w

    return mst, cost
