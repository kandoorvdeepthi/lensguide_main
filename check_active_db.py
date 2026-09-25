import os
from db.ps06_connection import DB_PATH, get_connection

print("ACTIVE DB:", os.path.abspath(DB_PATH))

conn = get_connection()

row = conn.execute("""
    SELECT poi_id, name, city_id, lat, lng, status
    FROM activities_poi
    WHERE poi_id = 'poi_cit_demo'
""").fetchone()

if row:
    print("CIT FOUND:")
    print(dict(row))
else:
    print("CIT NOT FOUND")

conn.close()