import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db" / "PS-06_CIT_DEMO.db"

print("=" * 70)
print("CIT DEMO DATABASE SCHEMA")
print("=" * 70)
print(f"Database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ---------------------------------------------------------
# TABLES
# ---------------------------------------------------------

tables = cur.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

print("\nTABLES")
print("=" * 70)

for (table_name,) in tables:

    print(f"\n📦 {table_name}")

    columns = cur.execute(
        f"PRAGMA table_info('{table_name}')"
    ).fetchall()

    for column in columns:

        cid, name, data_type, not_null, default_value, primary_key = column

        print(
            f"    {name:30} "
            f"TYPE={data_type:15} "
            f"NOT_NULL={not_null} "
            f"PK={primary_key} "
            f"DEFAULT={default_value}"
        )

# ---------------------------------------------------------
# FOREIGN KEYS
# ---------------------------------------------------------

print("\n\nFOREIGN KEYS")
print("=" * 70)

for (table_name,) in tables:

    foreign_keys = cur.execute(
        f"PRAGMA foreign_key_list('{table_name}')"
    ).fetchall()

    if foreign_keys:

        print(f"\n🔗 {table_name}")

        for fk in foreign_keys:

            print(
                f"    {fk[3]} "
                f"→ {fk[2]}.{fk[4]}"
            )

# ---------------------------------------------------------
# EXISTING ROW COUNTS
# ---------------------------------------------------------

print("\n\nROW COUNTS")
print("=" * 70)

for (table_name,) in tables:

    count = cur.execute(
        f"SELECT COUNT(*) FROM '{table_name}'"
    ).fetchone()[0]

    print(f"{table_name:30} {count}")

conn.close()

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)