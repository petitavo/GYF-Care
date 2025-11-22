import pandas as pd
import numpy as np
from db import db
from models import GraphNode, Patient, Hospital
from shared.config import Config
from graph.graph_utils import haversine

class GraphBuilder:

    def __init__(self):
        self.k = Config.K_NEIGHBORS
        self.nodes = []
        self.edges = {}   # dict: node_id → list of (neighbor, weight)

    def load_nodes_from_db(self):
        """Cargar pacientes y hospitales como nodos del grafo"""
        self.nodes = []

        # Pacientes → ID = p.code (P0001, P0002...)
        for p in Patient.query.all():
            self.nodes.append({
                "id": p.code,        # 👈 CAMBIO CLAVE
                "lat": p.lat,
                "lon": p.lon,
                "type": "patient"
            })

        # Hospitales → ID = h.code (H001, H002...)
        for h in Hospital.query.all():
            self.nodes.append({
                "id": h.code,        # 👈 CAMBIO CLAVE
                "lat": h.lat,
                "lon": h.lon,
                "type": "hospital"
            })

        print(f"✔️ Nodos cargados: {len(self.nodes)}")

    def build_knn_graph(self):
        """Construir grafo KNN usando distancia Haversine"""

        n = len(self.nodes)
        print(f"Construyendo grafo KNN con {n} nodos y k={self.k}")

        # Inicializar estructura
        self.edges = {node["id"]: [] for node in self.nodes}

        # Convertir coords a arrays
        coords = np.array([(node["lat"], node["lon"]) for node in self.nodes])

        # Matriz de distancias
        dist_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_matrix[i][j] = haversine(
                        coords[i][0], coords[i][1],
                        coords[j][0], coords[j][1]
                    )

        # Para cada nodo, elegir sus k vecinos más cercanos
        for i in range(n):
            distances = dist_matrix[i]
            nearest = np.argsort(distances)[:self.k]

            for j in nearest:
                node_from = self.nodes[i]["id"]
                node_to = self.nodes[j]["id"]
                weight = dist_matrix[i][j]

                self.edges[node_from].append((node_to, weight))

        print("✔️ Grafo KNN construido exitosamente.")
        return self.edges
