import networkx as nx
from graph.graph_utils import haversine

def min_cost_flow(patients, hospitals):
    G = nx.DiGraph()

    G.add_node("s")
    G.add_node("t")

    # Pacientes
    for p in patients:
        G.add_edge("s", p["id"], capacity=1, weight=0)

    # Hospitales
    for h in hospitals:
        G.add_edge(h["id"], "t", capacity=h["capacity"], weight=0)

    # Conexiones con costo = distancia
    for p in patients:
        for h in hospitals:
            d = haversine(p["lat"], p["lon"], h["lat"], h["lon"])
            G.add_edge(p["id"], h["id"], capacity=1, weight=int(d * 100))

    flow = nx.max_flow_min_cost(G, "s", "t")
    results = []

    for p in patients:
        for h in hospitals:
            if flow.get(p["id"], {}).get(h["id"], 0) == 1:
                dist = haversine(p["lat"], p["lon"], h["lat"], h["lon"])
                results.append({
                    "patient": p["id"],
                    "hospital": h["id"],
                    "dist_km": dist
                })

    return results
