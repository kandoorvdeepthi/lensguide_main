import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db" / "PS-06.db"

conn = sqlite3.connect(DB_PATH)

rows = conn.execute("""
    SELECT category_id, code, label, applies_to
    FROM categories
    WHERE LOWER(code) LIKE '%heritage%'
       OR LOWER(code) LIKE '%restaurant%'
       OR LOWER(code) LIKE '%cafe%'
       OR LOWER(code) LIKE '%food%'
       OR LOWER(code) LIKE '%landmark%'
       OR LOWER(label) LIKE '%heritage%'
       OR LOWER(label) LIKE '%restaurant%'
       OR LOWER(label) LIKE '%cafe%'
       OR LOWER(label) LIKE '%food%'
       OR LOWER(label) LIKE '%landmark%'
    ORDER BY code
""").fetchall()

print("=" * 70)
print("RELEVANT PS-06 CATEGORIES")
print("=" * 70)

if not rows:
    print("No matching categories found.")

for category_id, code, label, applies_to in rows:
    print(f"ID        : {category_id}")
    print(f"Code      : {code}")
    print(f"Label     : {label}")
    print(f"Applies to: {applies_to}")
    print("-" * 70)

conn.close()