import heapq

def prim(graph, start):
    visited = set()
    pq = []
    mst = []
    cost = 0

    visited.add(start)
    for v, w in graph[start]:
        heapq.heappush(pq, (w, start, v))

    while pq:
        w, u, v = heapq.heappop(pq)
        if v not in visited:
            visited.add(v)
            mst.append((u, v, w))
            cost += w

            for nxt, wt in graph[v]:
                if nxt not in visited:
                    heapq.heappush(pq, (wt, v, nxt))

    return mst, cost
