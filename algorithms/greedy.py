from graph.graph_utils import haversine

def greedy_assign(patients, hospitals):
    """
    patients: list {id, lat, lon}
    hospitals: list {id, lat, lon, capacity}
    """

    assignments = []

    for p in patients:
        best_h = None
        best_d = float("inf")

        for h in hospitals:
            if h["capacity"] <= 0:
                continue

            d = haversine(p["lat"], p["lon"], h["lat"], h["lon"])

            if d < best_d:
                best_d = d
                best_h = h

        if best_h:
            best_h["capacity"] -= 1
            assignments.append({
                "patient": p["id"],
                "hospital": best_h["id"],
                "dist_km": best_d
            })

    return assignments
