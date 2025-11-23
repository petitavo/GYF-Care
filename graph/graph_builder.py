import numpy as np

from models import Patient, Hospital
from shared.config import Config
from graph.graph_utils import haversine


class GraphBuilder:
    """
    Construye grafos geográficos a partir de pacientes y hospitales.

    Soporta tres modos principales:
      - KNN: cada nodo se conecta con sus k vecinos más cercanos.
      - RADIUS: se conecta solo si la distancia <= radio (km).
      - BIPARTITE_KNN: cada paciente se conecta a k hospitales más cercanos.
    """

    def __init__(self, k: int | None = None):
        # K por defecto viene de la configuración global
        self.k = k or Config.K_NEIGHBORS
        self.nodes: list[dict] = []
        # dict: node_id -> list[(neighbor_id, weight_km)]
        self.edges: dict[str, list[tuple[str, float]]] = {}

    # -----------------------------
    # Carga de nodos desde la BD
    # -----------------------------
    def load_nodes_from_db(self) -> None:
        """
        Carga TODOS los pacientes y hospitales como nodos del grafo.
        ID = code (P0001, H026, etc.)
        """
        self.nodes = []

        # Pacientes
        for p in Patient.query.all():
            self.nodes.append({
                "id": p.code,
                "lat": p.lat,
                "lon": p.lon,
                "type": "patient",
            })

        # Hospitales
        for h in Hospital.query.all():
            self.nodes.append({
                "id": h.code,
                "lat": h.lat,
                "lon": h.lon,
                "type": "hospital",
            })

        print(f"✔️ Nodos cargados en GraphBuilder: {len(self.nodes)}")

    def _ensure_nodes(self) -> None:
        """Si aún no se han cargado nodos, los carga desde la BD."""
        if not self.nodes:
            self.load_nodes_from_db()

    # -----------------------------
    # Utilidad interna: matriz de distancias
    # -----------------------------
    def _build_distance_matrix(self):
        """
        Construye la matriz de distancias geográficas entre TODOS los nodos.
        Devuelve:
          - n (int): número de nodos
          - coords (np.ndarray): [(lat, lon), ...]
          - dist_matrix (np.ndarray): n x n
        """
        self._ensure_nodes()
        n = len(self.nodes)

        coords = np.array([(node["lat"], node["lon"]) for node in self.nodes])
        dist_matrix = np.zeros((n, n), dtype=float)

        for i in range(n):
            for j in range(n):
                if i == j:
                    dist_matrix[i][j] = 0.0
                else:
                    lat1, lon1 = coords[i]
                    lat2, lon2 = coords[j]
                    dist_matrix[i][j] = haversine(lat1, lon1, lat2, lon2)

        return n, coords, dist_matrix

    # -----------------------------
    # 1) Grafo KNN geográfico
    # -----------------------------
    def build_knn_graph(self, k: int | None = None) -> dict:
        """
        Construye un grafo KNN clásico:
          - Cada nodo se conecta con sus k vecinos más cercanos.
        """
        if k is None:
            k = self.k

        self._ensure_nodes()
        n, _, dist_matrix = self._build_distance_matrix()

        # Inicializar estructura de aristas
        self.edges = {node["id"]: [] for node in self.nodes}

        for i in range(n):
            distances = dist_matrix[i]

            # argsort ordena de menor a mayor, incluído i mismo en posición 0
            # Tomamos los primeros k+1 y luego filtramos i.
            nearest_idx = np.argsort(distances)[:k + 1]

            for j in nearest_idx:
                if i == j:
                    continue
                node_from = self.nodes[i]["id"]
                node_to = self.nodes[j]["id"]
                weight = dist_matrix[i][j]

                self.edges[node_from].append((node_to, weight))

        print(f"✔️ Grafo KNN construido con k={k}. Nodos={n}, aristas={sum(len(v) for v in self.edges.values())}")
        return self.edges

    # -----------------------------
    # 2) Grafo por radio (ε-vecindario)
    # -----------------------------
    def build_radius_graph(self, radius_km: float) -> dict:
        """
        Construye un grafo donde se conecta una arista entre dos nodos
        solo si la distancia geográfica es <= radius_km.
        """
        self._ensure_nodes()
        n, _, dist_matrix = self._build_distance_matrix()

        self.edges = {node["id"]: [] for node in self.nodes}

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                d = dist_matrix[i][j]
                if d <= radius_km:
                    node_from = self.nodes[i]["id"]
                    node_to = self.nodes[j]["id"]
                    self.edges[node_from].append((node_to, d))

        print(f"✔️ Grafo por radio construido (R={radius_km} km). Nodos={n}, aristas={sum(len(v) for v in self.edges.values())}")
        return self.edges

    # -----------------------------
    # 3) Grafo bipartito KNN paciente→hospital
    # -----------------------------
    def build_bipartite_knn_graph(self, k: int | None = None) -> dict:
        """
        Construye un grafo bipartito donde:
          - Solo se crean aristas PACIENTE -> HOSPITAL.
          - Cada paciente se conecta con sus k hospitales más cercanos.
        """
        if k is None:
            k = self.k

        self._ensure_nodes()

        # Separar nodos por tipo
        patient_nodes = [n for n in self.nodes if n["type"] == "patient"]
        hospital_nodes = [n for n in self.nodes if n["type"] == "hospital"]

        self.edges = {node["id"]: [] for node in self.nodes}

        if not hospital_nodes:
            print("⚠️ No hay hospitales en la BD. Grafo bipartito vacío.")
            return self.edges

        # Para cada paciente, calcular distancia a todos los hospitales
        for p in patient_nodes:
            dists = []
            for h in hospital_nodes:
                d = haversine(p["lat"], p["lon"], h["lat"], h["lon"])
                dists.append((h["id"], d))

            # Ordenar hospitales por distancia y tomar k más cercanos
            dists.sort(key=lambda x: x[1])
            nearest_hospitals = dists[:k]

            for hid, d in nearest_hospitals:
                self.edges[p["id"]].append((hid, d))
                # Si quieres que sea completamente no dirigido, puedes agregar:
                # self.edges[hid].append((p["id"], d))

        print(f"✔️ Grafo bipartito KNN construido con k={k}. Pacientes={len(patient_nodes)}, hospitales={len(hospital_nodes)}")
        return self.edges
