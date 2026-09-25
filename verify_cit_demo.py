import sqlite3

DB_PATH = r"C:\Users\Sakshi Reddy\Desktop\lens_demo\db\PS-06_CIT_DEMO.db"

print("DATABASE:", DB_PATH)

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