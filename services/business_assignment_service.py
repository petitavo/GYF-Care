# services/business_assignment_service.py

from typing import Optional, Dict, Any, List, Tuple
from math import inf
import time

from db import db
from models import Patient, Hospital
from services.routing_service import RoutingService

# Algoritmos de asignación
from algorithms.greedy import greedy_assign
from algorithms.hungarian import hungarian
from algorithms.min_cost_flow import min_cost_flow

# Algoritmos de ruta
from algorithms.dijkstra import dijkstra
from algorithms.bellman_ford import bellman_ford

# Algoritmos de redes
from algorithms.kruskal import kruskal
from algorithms.prim import prim
from algorithms.edmonds_karp import edmonds_karp

# Distancia geográfica
from utils.geo_utils import distancia_km



class BusinessAssignmentService:
    """
    Servicio de alto nivel que integra:
      - Lógica de negocio (enfermedad → especialidad → hospitales candidatos).
      - Algoritmos de asignación (Greedy, Hungarian, Min-Cost Max-Flow).
      - Algoritmos de ruta (Dijkstra, Bellman-Ford) sobre el grafo KNN.
      - Algoritmos de redes (Kruskal, Prim, Edmonds-Karp) sobre el grafo.
    """

    def __init__(self):
        self.routing_service = RoutingService()
        self.graph = self.routing_service.get_graph()

    # ------------------------
    # 1. Inferir especialidad
    # ------------------------
    def infer_specialty(self, enfermedad: str) -> str:
        if not enfermedad:
            return "Medicina Interna"

        e = enfermedad.lower()

        mapping = {
            # Traumatología
            "fractura": "Traumatología",
            "luxación": "Traumatología",
            "traumatismo": "Traumatología",
            "tce": "Traumatología",

            # Cardiología
            "infarto": "Cardiología",
            "trombosis": "Cardiología",
            "hipertensión": "Cardiología",

            # Nefrología
            "renal": "Nefrología",
            "insuficiencia renal": "Nefrología",

            # Pediatría
            "niño": "Pediatría",
            "menor": "Pediatría",

            # Neumología
            "broncoespasmo": "Neumología",
            "neumonía": "Neumología",
        }

        for keyword, spec in mapping.items():
            if keyword in e:
                return spec

        return "Medicina Interna"

    # ------------------------
    # 2. Construir entrada (paciente + hospitales candidatos)
    # ------------------------
    def build_single_patient_inputs(
        self, patient_code: str
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Devuelve:
          - dict con datos del paciente
          - lista de hospitales candidatos (diccionarios)
        """
        patient: Patient = Patient.query.filter_by(code=patient_code).first()

        if not patient:
            raise ValueError(f"Paciente con code={patient_code} no existe")

        specialty = self.infer_specialty(patient.disease or "")

        # Filtrar hospitales por departamento (priorizar mismo) y especialidad
        hospitals_query = Hospital.query
        if patient.department:
            hospitals_query = hospitals_query.filter(
                Hospital.department == patient.department
            )

        hospitals_db = hospitals_query.all()

        spec_low = specialty.lower()
        candidates: List[Hospital] = [
            h for h in hospitals_db
            if h.specialties and spec_low in h.specialties.lower()
        ]

        # Si no hay con esa especialidad en su departamento, usar todos del depto
        if not candidates:
            candidates = hospitals_db

        # Y si aún así no hay, usar todos los hospitales del país
        if not candidates:
            candidates = Hospital.query.all()

        patient_dict = {
            "id": patient.code,  # importante: coincide con nodo en el grafo
            "code": patient.code,
            "lat": patient.lat,
            "lon": patient.lon,
            "severity": patient.severity,
            "department": patient.department,
            "disease": patient.disease,
            "specialty_required": specialty,
        }

        hospital_dicts = [{
            "id": h.code,       # importante: coincide con nodo en el grafo
            "code": h.code,
            "name": h.name,
            "lat": h.lat,
            "lon": h.lon,
            "department": h.department,
            "specialties": h.specialties,
            "capacity": h.capacity,
        } for h in candidates]

        return patient_dict, hospital_dicts

    # ------------------------
    # 3. Ejecutar algoritmos de asignación (3)
    # ------------------------
    def run_assignment_algorithms_for_patient(
        self,
        patient: Dict[str, Any],
        hospitals: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta Greedy, Hungarian y Min-Cost Max-Flow para ESTE paciente solo,
        usando la lista de hospitales candidatos.
        Retorna una lista con info de cada algoritmo.
        """
        patients_input = [patient]  # solo un paciente

        results: List[Dict[str, Any]] = []

        # Helper para encontrar la asignación concreta del paciente
        def find_assignment(assignments, patient_id: str):
            for a in assignments:
                if a.get("patient") == patient_id or a.get("patient_id") == patient_id:
                    return a
            return None

        # ---- 3.1 Greedy
        t0 = time.time()
        greedy_out = greedy_assign(patients_input, hospitals)
        t1 = time.time()
        greedy_asg = find_assignment(greedy_out, patient["id"])

        results.append({
            "name": "Greedy",
            "category": "Asignación",
            "big_o": "O(P·H)",
            "time_ms": (t1 - t0) * 1000.0,
            "raw_assignment": greedy_asg,
        })

        # ---- 3.2 Hungarian
        t0 = time.time()
        hung_out = hungarian(patients_input, hospitals)
        t1 = time.time()
        hung_asg = find_assignment(hung_out, patient["id"])

        results.append({
            "name": "Hungarian",
            "category": "Asignación",
            "big_o": "O(n^3)",
            "time_ms": (t1 - t0) * 1000.0,
            "raw_assignment": hung_asg,
        })

        # ---- 3.3 Min-Cost Max-Flow
        t0 = time.time()
        mcmf_out = min_cost_flow(patients_input, hospitals)
        t1 = time.time()
        mcmf_asg = find_assignment(mcmf_out, patient["id"])

        results.append({
            "name": "Min-Cost Max-Flow",
            "category": "Asignación",
            "big_o": "O(V^2·E)",
            "time_ms": (t1 - t0) * 1000.0,
            "raw_assignment": mcmf_asg,
        })

        return results

    # ------------------------
    # 4. Ejecutar algoritmos de ruta (2) para un par paciente-hospital
    # ------------------------
    def compute_path_algorithms(
        self,
        patient_id: str,
        hospital_id: str
    ) -> Dict[str, Any]:
        """
        Ejecuta Dijkstra y Bellman-Ford en el grafo KNN para el par
        (patient_id, hospital_id).
        """
        if patient_id not in self.graph or hospital_id not in self.graph:
            return {
                "dijkstra": None,
                "bellman_ford": None,
            }

        # Dijkstra
        t0 = time.time()
        dist_d, path_d = dijkstra(self.graph, patient_id, hospital_id)
        t1 = time.time()
        dijkstra_res = {
            "algorithm": "Dijkstra",
            "category": "Ruta más corta",
            "big_o": "O(E log V)",
            "time_ms": (t1 - t0) * 1000.0,
            "distance": dist_d,
            "path_nodes": path_d,
        }

        # Bellman-Ford
        t0 = time.time()
        dist_b, path_b = bellman_ford(self.graph, patient_id, hospital_id)
        t1 = time.time()
        bellman_res = {
            "algorithm": "Bellman-Ford",
            "category": "Ruta más corta",
            "big_o": "O(V·E)",
            "time_ms": (t1 - t0) * 1000.0,
            "distance": dist_b,
            "path_nodes": path_b,
        }

        return {
            "dijkstra": dijkstra_res,
            "bellman_ford": bellman_res,
        }

    # ------------------------
    # 5. Ejecutar algoritmos de redes (3) globales
    # ------------------------
    def run_network_algorithms(self) -> List[Dict[str, Any]]:
        """
        Ejecuta Kruskal, Prim y Edmonds-Karp sobre el grafo completo.
        Sirve para comparar tiempos/orden de complejidad.
        """
        results: List[Dict[str, Any]] = []

        # 5.1 Kruskal (MST)
        t0 = time.time()
        mst_k, cost_k = kruskal(self.graph)
        t1 = time.time()
        results.append({
            "name": "Kruskal",
            "category": "Redes / MST",
            "big_o": "O(E log V)",
            "time_ms": (t1 - t0) * 1000.0,
            "extra": {"mst_cost": cost_k},
        })

        # Para Prim necesitamos un nodo de inicio cualquiera
        if self.graph:
            any_node = next(iter(self.graph.keys()))
        else:
            any_node = None

        if any_node is not None:
            # 5.2 Prim (MST)
            t0 = time.time()
            mst_p, cost_p = prim(self.graph, any_node)
            t1 = time.time()
            results.append({
                "name": "Prim",
                "category": "Redes / MST",
                "big_o": "O(E log V)",
                "time_ms": (t1 - t0) * 1000.0,
                "extra": {"mst_cost": cost_p},
            })

        # 5.3 Edmonds-Karp (Flujo máximo) – armamos capacidades simples = 1
        # Elegimos dos nodos cualquiera distintos
        nodes_list = list(self.graph.keys())
        if len(nodes_list) >= 2:
            source = nodes_list[0]
            sink = nodes_list[1]

            capacity = {u: {} for u in self.graph}
            for u in self.graph:
                for v, _w in self.graph[u]:
                    capacity[u][v] = 1
                    if u not in capacity.get(v, {}):
                        capacity.setdefault(v, {})[u] = 0

            t0 = time.time()
            max_flow_val = edmonds_karp(capacity, source, sink)
            t1 = time.time()

            results.append({
                "name": "Edmonds-Karp",
                "category": "Redes / Flujo máximo",
                "big_o": "O(V·E^2)",
                "time_ms": (t1 - t0) * 1000.0,
                "extra": {
                    "source": source,
                    "sink": sink,
                    "max_flow": max_flow_val,
                },
            })

        return results

    # ------------------------
    # 6. Método principal para comparar los 8 algoritmos en un paciente
    # ------------------------
    def compare_all_algorithms_for_patient(self, patient_code: str) -> Dict[str, Any]:
        """
        Lógica principal:
          - Construye entrada (paciente + hospitales candidatos).
          - Ejecuta 3 algoritmos de asignación para ese paciente.
          - Para cada asignación, ejecuta 2 algoritmos de ruta (Dijkstra, Bellman-Ford).
          - Ejecuta 3 algoritmos de redes en el grafo completo.
          - Devuelve todo listo para que el front lo pinte.
        """
        patient, hospitals = self.build_single_patient_inputs(patient_code)
        patient_id = patient["id"]
        specialty = patient["specialty_required"]

        # Indexar hospitales por id para lookup rápido
        hospitals_by_id = {h["id"]: h for h in hospitals}

        # 1) Asignación
        assignment_algos_raw = self.run_assignment_algorithms_for_patient(patient, hospitals)

        assignment_algos_final = []

        for ar in assignment_algos_raw:
            asg = ar["raw_assignment"]

            if not asg:
                assignment_algos_final.append({
                    "name": ar["name"],
                    "category": ar["category"],
                    "big_o": ar["big_o"],
                    "time_ms": ar["time_ms"],
                    "hospital": None,
                    "distance_geo_km": None,
                    "paths": None,
                })
                continue

            hosp_id = asg.get("hospital") or asg.get("hospital_id")
            hosp = hospitals_by_id.get(hosp_id)

            if not hosp:
                assignment_algos_final.append({
                    "name": ar["name"],
                    "category": ar["category"],
                    "big_o": ar["big_o"],
                    "time_ms": ar["time_ms"],
                    "hospital": None,
                    "distance_geo_km": None,
                    "paths": None,
                })
                continue

            # Distancia geográfica directa
            d_geo = distancia_km(
                patient["lat"], patient["lon"],
                hosp["lat"], hosp["lon"]
            )

            # Rutas en el grafo KNN: Dijkstra vs Bellman-Ford
            path_results = self.compute_path_algorithms(patient_id, hosp_id)

            assignment_algos_final.append({
                "name": ar["name"],
                "category": ar["category"],
                "big_o": ar["big_o"],
                "time_ms": ar["time_ms"],
                "hospital": {
                    "id": hosp["id"],
                    "code": hosp["code"],
                    "name": hosp.get("name"),
                    "department": hosp.get("department"),
                    "lat": hosp["lat"],
                    "lon": hosp["lon"],
                    "specialties": hosp.get("specialties"),
                },
                "distance_geo_km": d_geo,
                "paths": path_results,
            })

        # 2) Redes (global, pero usamos ese mismo grafo)
        network_algos = self.run_network_algorithms()

        # 3) Armar respuesta final
        return {
            "patient": {
                "code": patient["code"],
                "severity": patient["severity"],
                "department": patient["department"],
                "disease": patient["disease"],
                "lat": patient["lat"],
                "lon": patient["lon"],
            },
            "specialty_required": specialty,
            "assignment_algorithms": assignment_algos_final,
            "network_algorithms": network_algos,
        }
