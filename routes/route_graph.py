# routes/route_graph.py

from flask import Blueprint, jsonify, request
import time

from shared.config import Config
from graph.graph_builder import GraphBuilder
from models import Patient, Hospital

graph_bp = Blueprint("graph", __name__, url_prefix="/api/graph")


def _build_nodes_response():
    """
    Devuelve listas de pacientes y hospitales con info básica
    para que el front pueda pintar el grafo.
    """
    patients_db = Patient.query.all()
    hospitals_db = Hospital.query.all()

    patients = [{
        "id": p.code,
        "code": p.code,
        "lat": p.lat,
        "lon": p.lon,
        "severity": p.severity,
        "disease": p.disease,
        "department": p.department,
        "type": "patient",
    } for p in patients_db]

    hospitals = [{
        "id": h.code,
        "code": h.code,
        "lat": h.lat,
        "lon": h.lon,
        "name": h.name,
        "specialties": h.specialties,
        "capacity": h.capacity,
        "department": h.department,
        "type": "hospital",
    } for h in hospitals_db]

    return patients, hospitals


def _edges_to_list(edges_dict: dict) -> list[dict]:
    """
    Convierte el dict {u: [(v, w), ...]} en una lista de aristas únicas:
      [
        {"source": "P0001", "target": "H026", "weight": 10.5},
        ...
      ]
    """
    edges = []
    seen = set()

    for u, neighbors in edges_dict.items():
        for v, w in neighbors:
            key = tuple(sorted((u, v)))
            if key in seen:
                continue
            seen.add(key)
            edges.append({
                "source": u,
                "target": v,
                "weight": w,
            })

    return edges


@graph_bp.get("/knn")
def graph_knn():
    """
    Devuelve el grafo KNN (K-Nearest Neighbors) usando el K de la configuración.

    ---
    tags:
      - Grafo
    responses:
      200:
        description: Grafo KNN completo
    """
    k = request.args.get("k", type=int) or Config.K_NEIGHBORS

    builder = GraphBuilder(k=k)
    builder.load_nodes_from_db()
    edges_dict = builder.build_knn_graph(k=k)

    patients, hospitals = _build_nodes_response()
    edges = _edges_to_list(edges_dict)

    return jsonify({
        "mode": "knn",
        "k": k,
        "patients": patients,
        "hospitals": hospitals,
        "edges": edges,
    })


@graph_bp.get("/radius")
def graph_radius():
    """
    Devuelve un grafo construido por radio:
      - Se conecta una arista si distancia <= radius (km).

    ---
    tags:
      - Grafo
    parameters:
      - in: query
        name: radius
        type: number
        required: false
        description: Radio en km (por defecto 50)
    responses:
      200:
        description: Grafo por radio
    """
    radius_km = request.args.get("radius", type=float) or 50.0

    builder = GraphBuilder()
    builder.load_nodes_from_db()
    edges_dict = builder.build_radius_graph(radius_km=radius_km)

    patients, hospitals = _build_nodes_response()
    edges = _edges_to_list(edges_dict)

    return jsonify({
        "mode": "radius",
        "radius_km": radius_km,
        "patients": patients,
        "hospitals": hospitals,
        "edges": edges,
    })


@graph_bp.get("/bipartite")
def graph_bipartite():
    """
    Devuelve un grafo BIPARTITO donde:
      - Solo hay aristas PACIENTE -> HOSPITAL.
      - Cada paciente se conecta a sus k hospitales más cercanos.

    ---
    tags:
      - Grafo
    parameters:
      - in: query
        name: k
        type: integer
        required: false
        description: Número de hospitales más cercanos por paciente (default = Config.K_NEIGHBORS)
    responses:
      200:
        description: Grafo bipartito paciente–hospital
    """
    k = request.args.get("k", type=int) or Config.K_NEIGHBORS

    builder = GraphBuilder(k=k)
    builder.load_nodes_from_db()
    edges_dict = builder.build_bipartite_knn_graph(k=k)

    patients, hospitals = _build_nodes_response()
    edges = _edges_to_list(edges_dict)

    return jsonify({
        "mode": "bipartite_knn",
        "k": k,
        "patients": patients,
        "hospitals": hospitals,
        "edges": edges,
    })


@graph_bp.get("/compare")
def graph_compare():
    """
    Compara los 3 algoritmos de creación de grafo:
      - KNN
      - RADIUS
      - BIPARTITE_KNN

    Devuelve tiempos, cantidad de aristas y grado promedio.
    Esto sirve para que puedas elegir cuál te conviene usar en tu app.

    ---
    tags:
      - Grafo
    parameters:
      - in: query
        name: k
        type: integer
        required: false
        description: K para KNN y bipartito (default = Config.K_NEIGHBORS)
      - in: query
        name: radius
        type: number
        required: false
        description: Radio en km para el grafo por radio (default = 50)
    responses:
      200:
        description: Comparación de constructores de grafo
    """
    k = request.args.get("k", type=int) or Config.K_NEIGHBORS
    radius_km = request.args.get("radius", type=float) or 50.0

    results = []

    # 1) KNN
    b1 = GraphBuilder(k=k)
    b1.load_nodes_from_db()
    t0 = time.time()
    edges_knn = b1.build_knn_graph(k=k)
    t1 = time.time()
    num_edges_knn = sum(len(v) for v in edges_knn.values())
    num_nodes = len(b1.nodes) if b1.nodes else 1
    results.append({
        "name": "knn",
        "k": k,
        "radius_km": None,
        "time_ms": (t1 - t0) * 1000.0,
        "num_nodes": num_nodes,
        "num_edges": num_edges_knn,
        "avg_degree": num_edges_knn / num_nodes,
    })

    # 2) RADIUS
    b2 = GraphBuilder()
    b2.load_nodes_from_db()
    t0 = time.time()
    edges_radius = b2.build_radius_graph(radius_km=radius_km)
    t1 = time.time()
    num_edges_radius = sum(len(v) for v in edges_radius.values())
    num_nodes_r = len(b2.nodes) if b2.nodes else 1
    results.append({
        "name": "radius",
        "k": None,
        "radius_km": radius_km,
        "time_ms": (t1 - t0) * 1000.0,
        "num_nodes": num_nodes_r,
        "num_edges": num_edges_radius,
        "avg_degree": num_edges_radius / num_nodes_r,
    })

    # 3) BIPARTITE_KNN
    b3 = GraphBuilder(k=k)
    b3.load_nodes_from_db()
    t0 = time.time()
    edges_bip = b3.build_bipartite_knn_graph(k=k)
    t1 = time.time()
    num_edges_bip = sum(len(v) for v in edges_bip.values())
    num_nodes_b = len(b3.nodes) if b3.nodes else 1
    results.append({
        "name": "bipartite_knn",
        "k": k,
        "radius_km": None,
        "time_ms": (t1 - t0) * 1000.0,
        "num_nodes": num_nodes_b,
        "num_edges": num_edges_bip,
        "avg_degree": num_edges_bip / num_nodes_b,
    })

    return jsonify({
        "k": k,
        "radius_km": radius_km,
        "graphs": results,
    })
