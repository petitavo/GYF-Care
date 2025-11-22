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
    Espera JSON como:
      { "patient_code": "P0001" }

    Responde con:
      - datos del paciente
      - especialidad requerida
      - para CADA algoritmo de asignación (Greedy, Hungarian, Min-Cost Max-Flow):
          - hospital asignado
          - distancia geográfica
          - Dijkstra vs Bellman-Ford (ruta y tiempos)
      - tiempos de Kruskal, Prim, Edmonds-Karp sobre el grafo.
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
        # Para depurar; en producción loguear en vez de exponer detail
        return jsonify({"error": "Error interno", "detail": str(ex)}), 500
