from flask import Blueprint, jsonify
import time

from db import db
from models import Patient, Hospital
from algorithms.greedy import greedy_assign
from algorithms.hungarian import hungarian
from algorithms.min_cost_flow import min_cost_flow

assignment_bp = Blueprint("assignments", __name__, url_prefix="/api/assign")


def load_data_from_db():
    patients = [{
        "id": f"P_{p.id}",
        "lat": p.lat,
        "lon": p.lon
    } for p in Patient.query.all()]

    hospitals = [{
        "id": f"H_{h.id}",
        "lat": h.lat,
        "lon": h.lon,
        "capacity": h.capacity
    } for h in Hospital.query.all()]

    return patients, hospitals


@assignment_bp.post("/greedy")
def assign_greedy():
    patients, hospitals = load_data_from_db()

    t0 = time.time()
    results = greedy_assign(patients, hospitals)
    t1 = time.time()

    return jsonify({
        "algorithm": "Greedy",
        "big_o": "O(PH)",
        "time_ms": (t1 - t0) * 1000,
        "assignments": results
    })


@assignment_bp.post("/hungarian")
def assign_hungarian():
    patients, hospitals = load_data_from_db()

    t0 = time.time()
    results = hungarian(patients, hospitals)
    t1 = time.time()

    return jsonify({
        "algorithm": "Hungarian",
        "big_o": "O(n^3)",
        "time_ms": (t1 - t0) * 1000,
        "assignments": results
    })


@assignment_bp.post("/mincostflow")
def assign_mincostflow():
    patients, hospitals = load_data_from_db()

    t0 = time.time()
    results = min_cost_flow(patients, hospitals)
    t1 = time.time()

    return jsonify({
        "algorithm": "Min-Cost Max-Flow",
        "big_o": "O(V^2 E)",
        "time_ms": (t1 - t0) * 1000,
        "assignments": results
    })
