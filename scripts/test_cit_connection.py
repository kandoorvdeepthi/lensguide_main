import sqlite3

DB = r".\db\PS-06_CIT_DEMO.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

row = conn.execute(
    """
    SELECT
        scene_id,
        entity_id,
        name,
        scene_type,
        real_scale_metres,
        supports_webxr,
        supports_ar_placement,
        status
    FROM xr_scenes
    WHERE entity_id = ?
    """,
    ("poi_cit_demo",)
).fetchone()

print("=" * 60)
print("CIT XR CONNECTION TEST")
print("=" * 60)

if row:
    print(dict(row))
else:
    print("NO XR SCENE FOUND")

print("=" * 60)

conn.close()