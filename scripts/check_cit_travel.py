import sqlite3

DB_PATH = r".\db\PS-06_CIT_DEMO.db"

conn = sqlite3.connect(DB_PATH)

print("=" * 60)
print("CIT TRAVEL MATRIX")
print("=" * 60)

rows = conn.execute("""
    SELECT *
    FROM poi_travel_matrix
""").fetchall()

for row in rows:
    print(row)

print("-" * 60)
print("TOTAL ROWS:", len(rows))

conn.close()