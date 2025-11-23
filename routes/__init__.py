# routes/__init__.py

from .route_paths import path_bp
from .route_assignments import assignment_bp
from .route_network import network_bp
from .route_compare import compare_bp
from .route_business import business_bp
from .route_graph import graph_bp

__all__ = [
    "path_bp",
    "assignment_bp",
    "network_bp",
    "compare_bp",
    "business_bp",
    "graph_bp",
]
