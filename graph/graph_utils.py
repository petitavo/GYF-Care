from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en KM

    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)

    a = (
        sin(dLat/2)**2 +
        cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    )
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c
