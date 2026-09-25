import sqlite3
import math

DB = r".\db\PS-06_CIT_DEMO.db"

LABEL = "poi_cit_demo"
USER_LAT = 13.012338
USER_LNG = 77.703378


def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlng / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


conn = sqlite3.connect(DB)

rows = conn.execute(
    """
    SELECT poi_id, name, lat, lng
    FROM activities_poi
    """
).fetchall()

print("=" * 60)
print("CIT POI RESOLUTION TEST")
print("=" * 60)

best = None

for poi_id, name, lat, lng in rows:
    distance = haversine_km(
        USER_LAT,
        USER_LNG,
        lat,
        lng
    )

    print(
        f"{poi_id} | {name} | "
        f"{distance:.3f} km"
    )

    if best is None or distance < best[0]:
        best = (distance, poi_id, name)

print("-" * 60)

if best:
    print("RESOLVED POI:")
    print("poi_id:", best[1])
    print("name:", best[2])
    print("distance_km:", round(best[0], 3))

print("=" * 60)

conn.close()