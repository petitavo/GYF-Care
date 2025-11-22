from flask import Blueprint, jsonify
import time

from services.routing_service import RoutingService
from algorithms.kruskal import kruskal
from algorithms.prim import prim
from algorithms.edmonds_karp import edmonds_karp

network_bp = Blueprint("network", __name__, url_prefix="/api/network")

_network_routing = None
_network_graph_cache = None


def get_network_graph():
    global _network_routing, _network_graph_cache
    if _network_graph_cache is None:
        _network_routing = RoutingService()
        _network_graph_cache = _network_routing.get_graph()
    return _network_graph_cache


@network_bp.get("/kruskal")
def mst_kruskal():
    graph = get_network_graph()

    t0 = time.time()
    mst, cost = kruskal(graph)
    t1 = time.time()

    return jsonify({
        "algorithm": "Kruskal",
        "big_o": "O(E log V)",
        "time_ms": (t1 - t0) * 1000,
        "cost_total": cost,
        "edges": mst,
    })


@network_bp.get("/prim/<start>")
def mst_prim(start):
    graph = get_network_graph()

    t0 = time.time()
    mst, cost = prim(graph, start)
    t1 = time.time()

    return jsonify({
        "algorithm": "Prim",
        "big_o": "O(E log V)",
        "time_ms": (t1 - t0) * 1000,
        "cost_total": cost,
        "edges": mst,
    })


@network_bp.get("/flow/<source>/<sink>")
def max_flow(source, sink):
    graph = get_network_graph()

    # Construir matriz de capacidades a partir del grafo KNN
    capacity = {u: {} for u in graph}
    for u in graph:
        for v, _w in graph[u]:
            capacity[u][v] = 1
            if u not in capacity.get(v, {}):
                capacity.setdefault(v, {})[u] = 0

    t0 = time.time()
    result = edmonds_karp(capacity, source, sink)
    t1 = time.time()

    return jsonify({
        "algorithm": "Edmonds-Karp",
        "big_o": "O(V·E^2)",
        "time_ms": (t1 - t0) * 1000,
        "max_flow": result,
    })
