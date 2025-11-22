from flask import Blueprint, jsonify
import time

from services.routing_service import RoutingService
from algorithms.dijkstra import dijkstra
from algorithms.bellman_ford import bellman_ford
from algorithms.floyd_warshall import floyd_warshall, get_fw_path

path_bp = Blueprint("paths", __name__, url_prefix="/api/path")

_routing_service = None
_graph_cache = None


def get_graph():
    """
    Construye el grafo la primera vez que se llama
    y luego reutiliza la misma instancia (cache en memoria).
    """
    global _routing_service, _graph_cache
    if _graph_cache is None:
        _routing_service = RoutingService()
        _graph_cache = _routing_service.get_graph()
    return _graph_cache


@path_bp.get("/dijkstra/<start>/<end>")
def path_dijkstra(start, end):
    graph = get_graph()

    t0 = time.time()
    dist, path = dijkstra(graph, start, end)
    t1 = time.time()

    return jsonify({
        "algorithm": "Dijkstra",
        "big_o": "O(E log V)",
        "time_ms": (t1 - t0) * 1000,
        "distance": dist,
        "path": path,
    })


@path_bp.get("/bellman/<start>/<end>")
def path_bellman(start, end):
    graph = get_graph()

    t0 = time.time()
    dist, path = bellman_ford(graph, start, end)
    t1 = time.time()

    return jsonify({
        "algorithm": "Bellman-Ford",
        "big_o": "O(V·E)",
        "time_ms": (t1 - t0) * 1000,
        "distance": dist,
        "path": path,
    })


@path_bp.get("/floyd/<start>/<end>")
def path_floyd(start, end):
    """
    OJO: Floyd-Warshall es O(n^3). Si el grafo es muy grande
    puede demorar bastante. Si pasa, conviene limitar a subgrafo.
    """
    graph = get_graph()

    t0 = time.time()
    nodes, dist_matrix, next_hop = floyd_warshall(graph)
    path = get_fw_path(start, end, nodes, next_hop)

    dist = None
    if path:
        i = nodes.index(start)
        j = nodes.index(end)
        dist = float(dist_matrix[i][j])

    t1 = time.time()

    return jsonify({
        "algorithm": "Floyd-Warshall",
        "big_o": "O(n^3)",
        "time_ms": (t1 - t0) * 1000,
        "distance": dist,
        "path": path,
    })
