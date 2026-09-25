import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db" / "PS-06_CIT_DEMO.db"

TABLES = [
    "activities_poi",
    "poi_facts_kb",
    "place_kb",
    "poi_media",
    "landmark_image_set",
    "poi_travel_matrix",
    "xr_scenes",
]

conn = sqlite3.connect(DB_PATH)

print("=" * 80)
print("EXACT SEED TABLE SCHEMAS")
print("=" * 80)

for table in TABLES:

    print("\n" + "=" * 80)
    print(f"TABLE: {table}")
    print("=" * 80)

    columns = conn.execute(
        f"PRAGMA table_info('{table}')"
    ).fetchall()

    for row in columns:
        cid, name, data_type, not_null, default_value, primary_key = row

        print(
            f"{cid:2} | "
            f"{name:30} | "
            f"{data_type:18} | "
            f"NOT NULL={not_null} | "
            f"PK={primary_key} | "
            f"DEFAULT={default_value}"
        )

    foreign_keys = conn.execute(
        f"PRAGMA foreign_key_list('{table}')"
    ).fetchall()

    if foreign_keys:
        print("\nFOREIGN KEYS:")

        for fk in foreign_keys:
            print(
                f"  {fk[3]} -> {fk[2]}.{fk[4]}"
            )

    count = conn.execute(
        f"SELECT COUNT(*) FROM '{table}'"
    ).fetchone()[0]

    print(f"\nCURRENT ROW COUNT: {count}")

conn.close()

print("\n" + "=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)