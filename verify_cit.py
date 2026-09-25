import sqlite3
import os

from db.ps06_connection import DB_PATH

print("DATABASE:", os.path.abspath(DB_PATH))

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

cursor.execute("""
    SELECT poi_id, name, city_id, lat, lng, status
    FROM activities_poi
    WHERE LOWER(name) LIKE '%cambridge%'
       OR LOWER(name) LIKE '%institute of technology%'
""")

rows = cursor.fetchall()

print("CANDIDATES:", len(rows))

for row in rows:
    print(dict(row))

conn.close()