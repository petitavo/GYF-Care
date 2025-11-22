from flask import Blueprint, jsonify
import time

from services.routing_service import RoutingService
from db import db
from models import Patient, Hospital

from algorithms.dijkstra import dijkstra
from algorithms.bellman_ford import bellman_ford
from algorithms.floyd_warshall import floyd_warshall, get_fw_path

from algorithms.greedy import greedy_assign
from algorithms.hungarian import hungarian
from algorithms.min_cost_flow import min_cost_flow

from algorithms.kruskal import kruskal
from algorithms.prim import prim
from algorithms.edmonds_karp import edmonds_karp

compare_bp = Blueprint("compare", __name__, url_prefix="/api/compare")

_routing_service = None
_graph_cache = None


def get_graph():
    global _routing_service, _graph_cache
    if _graph_cache is None:
        _routing_service = RoutingService()
        _graph_cache = _routing_service.get_graph()
    return _graph_cache


def load_data_from_db():
    """Carga pacientes y hospitales para los algoritmos de asignación."""
    patients = [{
        "id": f"P_{p.id}",
        "lat": p.lat,
        "lon": p.lon,
    } for p in Patient.query.all()]

    hospitals = [{
        "id": f"H_{h.id}",
        "lat": h.lat,
        "lon": h.lon,
        "capacity": h.capacity,
    } for h in Hospital.query.all()]

    return patients, hospitals


@compare_bp.get("/all/<start>/<end>")
def compare_all(start, end):
    """
    Compara los 9 algoritmos principales.
    start y end son IDs de nodos del grafo: ej. 'P_1', 'H_3'
    """
    graph = get_graph()
    results = {
        "paths": [],
        "assignment": [],
        "network": [],
    }

    # ======================
    #  A) ALGORITMOS DE RUTA
    # ======================

    # 1) Dijkstra
    t0 = time.time()
    _dist_d, _path_d = dijkstra(graph, start, end)
    t1 = time.time()
    results["paths"].append({
        "algorithm": "Dijkstra",
        "category": "Ruta más corta",
        "big_o": "O(E log V)",
        "time_ms": (t1 - t0) * 1000,
    })

    # 2) Bellman-Ford
    t0 = time.time()
    _dist_b, _path_b = bellman_ford(graph, start, end)
    t1 = time.time()
    results["paths"].append({
        "algorithm": "Bellman-Ford",
        "category": "Ruta más corta",
        "big_o": "O(V·E)",
        "time_ms": (t1 - t0) * 1000,
    })

    # 3) Floyd-Warshall
    # OJO: puede ser pesado con muchos nodos. Si se tarda demasiado,
    # puedes limitar el grafo a un subconjunto de nodos.
    #t0 = time.time()
   #nodes, dist_matrix, next_hop = floyd_warshall(graph)
    #_ = get_fw_path(start, end, nodes, next_hop)
    #t1 = time.time()
    #results["paths"].append({
       # "algorithm": "Floyd-Warshall",
      #  "category": "Ruta más corta",
     #   "big_o": "O(n^3)",
    #    "time_ms": (t1 - t0) * 1000,
   # })

    # ========================
    #  B) ALGORITMOS ASIGNACIÓN
    # ========================
    patients, hospitals = load_data_from_db()

    # 4) Greedy
    t0 = time.time()
    _asg_greedy = greedy_assign(patients, hospitals)
    t1 = time.time()
    results["assignment"].append({
        "algorithm": "Greedy",
        "category": "Asignación pacientes-hospitales",
        "big_o": "O(P·H)",
        "time_ms": (t1 - t0) * 1000,
    })

    # 5) Hungarian
    t0 = time.time()
    _asg_hungarian = hungarian(patients, hospitals)
    t1 = time.time()
    results["assignment"].append({
        "algorithm": "Hungarian",
        "category": "Asignación pacientes-hospitales",
        "big_o": "O(n^3)",
        "time_ms": (t1 - t0) * 1000,
    })

    # 6) Min-Cost Max-Flow
    t0 = time.time()
    _asg_mcmf = min_cost_flow(patients, hospitals)
    t1 = time.time()
    results["assignment"].append({
        "algorithm": "Min-Cost Max-Flow",
        "category": "Asignación pacientes-hospitales",
        "big_o": "O(V^2·E)",
        "time_ms": (t1 - t0) * 1000,
    })

    # =========================
    #  C) REDES / MST / FLUJO
    # =========================

    # 7) Kruskal
    t0 = time.time()
    _mst_k, _cost_k = kruskal(graph)
    t1 = time.time()
    results["network"].append({
        "algorithm": "Kruskal",
        "category": "MST / Redes",
        "big_o": "O(E log V)",
        "time_ms": (t1 - t0) * 1000,
    })

    # 8) Prim (usando start como raíz)
    t0 = time.time()
    _mst_p, _cost_p = prim(graph, start)
    t1 = time.time()
    results["network"].append({
        "algorithm": "Prim",
        "category": "MST / Redes",
        "big_o": "O(E log V)",
        "time_ms": (t1 - t0) * 1000,
    })

    # 9) Edmonds-Karp (Max Flow) - capacidad fija 1 por arista
    capacity = {u: {} for u in graph}
    for u in graph:
        for v, _w in graph[u]:
            capacity[u][v] = 1
            if u not in capacity.get(v, {}):
                capacity.setdefault(v, {})[u] = 0

    t0 = time.time()
    _max_flow = edmonds_karp(capacity, start, end)
    t1 = time.time()
    results["network"].append({
        "algorithm": "Edmonds-Karp",
        "category": "Flujo máximo",
        "big_o": "O(V·E^2)",
        "time_ms": (t1 - t0) * 1000,
    })

    return jsonify(results)
