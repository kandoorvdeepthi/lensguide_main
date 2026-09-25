import sqlite3

DB = r".\db\PS-06_CIT_DEMO.db"

conn = sqlite3.connect(DB)

rows = conn.execute("""
    SELECT
        scene_id,
        entity_id,
        name,
        scene_type,
        supports_ar_placement,
        status
    FROM xr_scenes
""").fetchall()

print("=" * 60)
print("CIT XR SCENES")
print("=" * 60)

for row in rows:
    print(row)

print("=" * 60)

conn.close()