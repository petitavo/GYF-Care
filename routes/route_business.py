# routes/route_business.py

from flask import Blueprint, jsonify, request
from db import db
from models import Patient, Hospital
from services.business_assignment_service import BusinessAssignmentService

business_bp = Blueprint("business", __name__, url_prefix="/api")

_service = None


def get_service():
    global _service
    if _service is None:
        _service = BusinessAssignmentService()
    return _service


@business_bp.get("/patients")
def list_patients():
    """
    Lista todos los pacientes registrados en la base de datos.

    ---
    tags:
      - Pacientes
    responses:
      200:
        description: Lista de pacientes
        schema:
          type: array
          items:
            type: object
            properties:
              code:
                type: string
                example: P0001
              severity:
                type: string
                example: Leve
              department:
                type: string
                example: Junín
              disease:
                type: string
                example: Hepatitis A
              lat:
                type: number
                format: float
                example: -10.75014
              lon:
                type: number
                format: float
                example: -76.474577
    """
    patients = Patient.query.all()
    data = [{
        "code": p.code,
        "severity": p.severity,
        "department": p.department,
        "disease": p.disease,
        "lat": p.lat,
        "lon": p.lon,
    } for p in patients]

    return jsonify(data)


@business_bp.get("/hospitals")
def list_hospitals():
    """
    Lista todos los hospitales registrados en la base de datos.

    ---
    tags:
      - Hospitales
    responses:
      200:
        description: Lista de hospitales
        schema:
          type: array
          items:
            type: object
            properties:
              code:
                type: string
                example: H001
              name:
                type: string
                example: Hospital I Lampa - EsSalud - Red Asistencial Juliaca
              department:
                type: string
                example: Puno
              lat:
                type: number
                format: float
                example: -15.36421167
              lon:
                type: number
                format: float
                example: -70.36700167
              specialties:
                type: string
                example: Medicina General, Cirugía, Pediatría
              capacity:
                type: integer
                example: 10
    """
    hospitals = Hospital.query.all()
    data = [{
        "code": h.code,
        "name": h.name,
        "department": h.department,
        "lat": h.lat,
        "lon": h.lon,
        "specialties": h.specialties,
        "capacity": h.capacity,
    } for h in hospitals]

    return jsonify(data)


@business_bp.post("/assign/compare-patient")
def assign_compare_patient():
    """
    Compara TODOS los algoritmos para un solo paciente.

    Para un paciente dado (por su código), ejecuta:
      - 3 algoritmos de asignación (Greedy, Hungarian, Min-Cost Max-Flow)
      - Para cada asignación, 2 algoritmos de ruta (Dijkstra, Bellman-Ford)
      - 3 algoritmos de redes (Kruskal, Prim, Edmonds-Karp)

    Devuelve:
      - Datos del paciente
      - Especialidad requerida
      - Para cada algoritmo de asignación:
          * hospital asignado (si lo hay)
          * distancia geográfica paciente-hospital
          * rutas Dijkstra y Bellman-Ford en el grafo KNN
      - Tiempos de los algoritmos de redes

    ---
    tags:
      - Asignación
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            patient_code:
              type: string
              example: P0001
    responses:
      200:
        description: Resultados de comparación de algoritmos para el paciente
        schema:
          type: object
          properties:
            patient:
              type: object
            specialty_required:
              type: string
            assignment_algorithms:
              type: array
              items:
                type: object
            network_algorithms:
              type: array
              items:
                type: object
      400:
        description: Petición inválida (falta patient_code)
      404:
        description: Paciente no encontrado
    """
    body = request.get_json(silent=True) or {}
    patient_code = body.get("patient_code") or body.get("id_paciente")

    if not patient_code:
        return jsonify({
            "error": "Debe enviar 'patient_code' (ej. 'P0001')"
        }), 400

    service = get_service()

    try:
        result = service.compare_all_algorithms_for_patient(patient_code)
        return jsonify(result)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as ex:
        # Para debug; en producción loguear en vez de mostrar detail
        return jsonify({"error": "Error interno", "detail": str(ex)}), 500


@business_bp.post("/assign/patient-best")
def assign_patient_best():
    """
    Asigna un solo paciente a un hospital "final" usando lógica de negocio
    y algoritmos de asignación en este orden de prioridad:
      1) Min-Cost Max-Flow
      2) Hungarian
      3) Greedy

    Además devuelve:
      - Distancia geográfica paciente-hospital
      - Ruta Dijkstra y Bellman-Ford en el grafo KNN

    ---
    tags:
      - Asignación
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            patient_code:
              type: string
              example: P0001
    responses:
      200:
        description: Asignación final de hospital para el paciente
        schema:
          type: object
          properties:
            patient:
              type: object
            specialty_required:
              type: string
            algorithm_used:
              type: object
            hospital:
              type: object
            distance_geo_km:
              type: number
            paths:
              type: object
      400:
        description: Petición inválida (falta patient_code)
      404:
        description: Paciente no encontrado o sin hospital asignable
    """
    body = request.get_json(silent=True) or {}
    patient_code = body.get("patient_code") or body.get("id_paciente")

    if not patient_code:
        return jsonify({
            "error": "Debe enviar 'patient_code' (ej. 'P0001')"
        }), 400

    service = get_service()

    try:
        # Usamos el método que definimos en el servicio para elegir un hospital definitivo
        result = service.assign_best_hospital_for_patient(patient_code)
        return jsonify(result)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as ex:
        return jsonify({"error": "Error interno", "detail": str(ex)}), 500
