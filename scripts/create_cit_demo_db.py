import sqlite3
from pathlib import Path

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_DB = PROJECT_ROOT / "db" / "PS-06.db"
DEMO_DB = PROJECT_ROOT / "db" / "PS-06_CIT_DEMO.db"

print("=" * 70)
print("CREATING CIT DEMO DATABASE")
print("=" * 70)

print(f"Source database : {SOURCE_DB}")
print(f"Demo database   : {DEMO_DB}")

# ---------------------------------------------------------
# SAFETY CHECKS
# ---------------------------------------------------------

if not SOURCE_DB.exists():
    raise FileNotFoundError(
        f"Original PS-06 database not found:\n{SOURCE_DB}"
    )

if DEMO_DB.exists():
    raise FileExistsError(
        f"Demo database already exists:\n{DEMO_DB}\n"
        "Delete it manually only if you intentionally want to recreate it."
    )

# ---------------------------------------------------------
# CONNECT
# ---------------------------------------------------------

source = sqlite3.connect(SOURCE_DB)
demo = sqlite3.connect(DEMO_DB)

try:

    # Get the complete SQLite schema.
    schema_objects = source.execute("""
        SELECT type, name, sql
        FROM sqlite_master
        WHERE sql IS NOT NULL
          AND type IN ('table', 'index', 'trigger', 'view')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY
            CASE type
                WHEN 'table' THEN 1
                WHEN 'index' THEN 2
                WHEN 'trigger' THEN 3
                WHEN 'view' THEN 4
                ELSE 5
            END,
            name
    """).fetchall()

    print("\nCopying schema...")

    for object_type, name, sql in schema_objects:

        try:
            demo.execute(sql)
            print(f"  ✓ {object_type}: {name}")

        except sqlite3.OperationalError as error:
            print(
                f"  ⚠ Could not create "
                f"{object_type} '{name}': {error}"
            )

    demo.commit()

finally:
    source.close()
    demo.close()

print("\n" + "=" * 70)
print("CIT DEMO DATABASE CREATED")
print("=" * 70)

print(f"\nCreated:")
print(DEMO_DB)

print("\nIMPORTANT:")
print("Only the database schema was copied.")
print("No CIT testing data has been inserted yet.")
print("The original PS-06.db was NOT modified.")