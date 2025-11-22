from app import app
from services.routing_service import RoutingService

with app.app_context():
    rs = RoutingService()
    graph = rs.get_graph()
    print("Total nodos en grafo:", len(graph))
    print("Algunos nodos:", list(graph.keys())[:20])
