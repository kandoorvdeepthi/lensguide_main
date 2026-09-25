import sqlite3
import os
from decimal import Decimal

# CIT demo database
DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "PS-06_CIT_DEMO.db"
)

# Path to PS-06.db — sits at project root, alongside main.py
DB_PATH = os.getenv(
    "LENS_DB_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "PS-06.db"
    )
)

def get_connection():
    """
    Opens a fresh connection with Row factory so results
    come back as dict-like objects instead of plain tuples.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    """Convert sqlite3.Row to plain dict."""
    return dict(row) if row else None


def rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows]


# ─────────────────────────────────────────
# 1. Find POI by label_class (from Gemini)
# ─────────────────────────────────────────
def get_poi_by_label_class(label_class: str) -> dict | None:
    """
    landmark_image_set.label_class is a CLOSED recognition class
    (39 total), not always unique to one POI — e.g. 'watchtower_terrace'
    exists in 3 different cities in PS-06. When multiple POIs share
    a class, we deterministically pick the one with the highest
    popularity_score, so results are stable across calls.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT l.poi_id
            FROM landmark_image_set l
            JOIN activities_poi a ON a.poi_id = l.poi_id
            WHERE l.label_class = ?
            ORDER BY a.popularity_score DESC
            LIMIT 1
            """,
            (label_class,),
        )
        row = cur.fetchone()
        if not row or not row["poi_id"]:
            return None

        return get_poi_by_id(row["poi_id"])
    finally:
        conn.close()


def get_all_label_classes():
    """
    Returns the closed set of 39 recognition classes, with one
    representative POI's name/city/category/description per class.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.label_class, a.name, c.name AS city_name,
                   a.poi_category, a.description
            FROM landmark_image_set l
            JOIN activities_poi a ON a.poi_id = l.poi_id
            JOIN cities c ON c.city_id = a.city_id
            GROUP BY l.label_class
            ORDER BY l.label_class
        """)
        return rows_to_list(cur.fetchall())
    finally:
        conn.close()

# ─────────────────────────────────────────
# 2. Get full POI row by poi_id
# ─────────────────────────────────────────
def get_poi_by_id(poi_id: str) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.*, c.name AS city_name, c.state AS city_state,
                   c.primary_language AS city_language,
                   co.name AS country_name
            FROM activities_poi a
            JOIN cities c ON c.city_id = a.city_id
            JOIN countries co ON co.country_id = c.country_id
            WHERE a.poi_id = ?
            """,
            (poi_id,),
        )
        row = cur.fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


# ─────────────────────────────────────────
# 3. Fuzzy name search (fallback, for testing
#    before Gemini is retrained on label_class)
# ─────────────────────────────────────────
def search_poi_by_name(name: str) -> dict | None:
    """
    Temporary bridge: Gemini currently returns a free-text NAME.
    This does a LIKE match against activities_poi.name until
    the vision agent is updated to predict label_class directly.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.*, c.name AS city_name, c.state AS city_state,
                   c.primary_language AS city_language,
                   co.name AS country_name
            FROM activities_poi a
            JOIN cities c ON c.city_id = a.city_id
            JOIN countries co ON co.country_id = c.country_id
            WHERE a.name LIKE ?
            LIMIT 1
            """,
            (f"%{name}%",),
        )
        row = cur.fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


# ─────────────────────────────────────────
# 4. Facts for a POI (poi_facts_kb), by language
# ─────────────────────────────────────────
def get_facts(poi_id: str, language: str = "en-IN") -> list[dict]:
    """
    language must be a BCP-47 tag: 'en-IN', 'hi', 'ta' etc.
    Falls back to en-IN if the requested language has no rows.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT fact_id, fact_type, fact_text, confidence,
                   display_priority, language
            FROM poi_facts_kb
            WHERE poi_id = ? AND language = ?
            ORDER BY display_priority ASC
            """,
            (poi_id, language),
        )
        rows = rows_to_list(cur.fetchall())

        if not rows and language != "en-IN":
            cur.execute(
                """
                SELECT fact_id, fact_type, fact_text, confidence,
                       display_priority, language
                FROM poi_facts_kb
                WHERE poi_id = ? AND language = 'en-IN'
                ORDER BY display_priority ASC
                """,
                (poi_id,),
            )
            rows = rows_to_list(cur.fetchall())

        return rows
    finally:
        conn.close()


# ─────────────────────────────────────────
# 5. Place knowledge chunks (place_kb), by section/language
# ─────────────────────────────────────────
def get_place_kb(
    poi_id: str = None,
    city_id: str = None,
    language: str = "en-IN",
    section: str = None,
) -> list[dict]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = """
            SELECT chunk_id, section, title, body, language, seasonal_relevance
            FROM place_kb
            WHERE language = ?
        """
        params = [language]

        if poi_id:
            query += " AND poi_id = ?"
            params.append(poi_id)
        if city_id:
            query += " AND city_id = ?"
            params.append(city_id)
        if section:
            query += " AND section = ?"
            params.append(section)

        cur.execute(query, params)
        rows = rows_to_list(cur.fetchall())

        if not rows and language != "en-IN":
            return get_place_kb(poi_id, city_id, "en-IN", section)

        return rows
    finally:
        conn.close()


# ─────────────────────────────────────────
# 6. Nearby POIs via poi_travel_matrix
# ─────────────────────────────────────────
def get_nearby(poi_id, mode="walk", limit=3):
    """
    Enriched vs the earlier version: now also selects opens_at,
    closes_at, description and status (all real activities_poi
    columns, nothing invented), and excludes the origin POI
    itself plus any inactive destination — matches requirements
    3, 4, 5 exactly.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.matrix_id, m.mode, m.minutes, m.distance_km,
                   m.carbon_kg, m.cost, m.currency, m.bearing_deg,
                   d.poi_id AS dest_poi_id, d.name AS dest_name,
                   d.poi_category, d.popularity_score, d.entry_cost,
                   d.currency AS dest_currency, d.opens_at, d.closes_at,
                   d.description, d.status, d.lat, d.lng
            FROM poi_travel_matrix m
            JOIN activities_poi d ON d.poi_id = m.dest_poi_id
            WHERE m.origin_poi_id = ?
              AND m.mode = ?
              AND m.dest_poi_id != m.origin_poi_id
              AND d.status = 'active'
            ORDER BY m.minutes ASC
            LIMIT ?
        """, (poi_id, mode, limit))
        return rows_to_list(cur.fetchall())
    finally:
        conn.close()

# ─────────────────────────────────────────
# 7. Menu/sign ground truth lookup (for scoring/dev only)
# ─────────────────────────────────────────
def get_menu_sign_reference(image_id: str = None, city_id: str = None) -> list[dict]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if image_id:
            cur.execute(
                "SELECT * FROM menu_sign_images WHERE image_id = ?", (image_id,)
            )
        elif city_id:
            cur.execute(
                "SELECT * FROM menu_sign_images WHERE city_id = ? LIMIT 10",
                (city_id,),
            )
        else:
            cur.execute("SELECT * FROM menu_sign_images LIMIT 10")
        return rows_to_list(cur.fetchall())
    finally:
        conn.close()


# ─────────────────────────────────────────
# 8. XR scene lookup for a POI
# ─────────────────────────────────────────
def get_xr_scene(poi_id: str) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM xr_scenes
            WHERE entity_type = 'poi' AND entity_id = ?
              AND supports_ar_placement = 1
              AND status = 'active'
            LIMIT 1
            """,
            (poi_id,),
        )
        row = cur.fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


# ─────────────────────────────────────────
# Money helper — never use float()
# ─────────────────────────────────────────
def format_money(amount_text: str, currency: str) -> dict:
    """
    amount_text comes from the DB as TEXT, e.g. '750.00'.
    Returns both the exact Decimal-safe string and currency,
    per PS-06 Rule R3 (money is a pair, never a float).
    """
    decimal_value = Decimal(amount_text)  # exact, no float roundtrip
    return {
        "amount": str(decimal_value),
        "currency": currency,
        "is_free": decimal_value == Decimal("0.00"),
    }

def resolve_poi_by_label_and_location(
    label_class: str,
    user_latitude: float | None,
    user_longitude: float | None,
) -> dict | None:
    """
    Resolve a PS-06 recognition class to the nearest POI using GPS.
    """

    import math

    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT DISTINCT
                a.poi_id,
                a.name,
                a.city_id,
                a.lat,
                a.lng
            FROM landmark_image_set l
            JOIN activities_poi a ON a.poi_id = l.poi_id
            WHERE l.label_class = ?
            """,
            (label_class,),
        )

        rows = cur.fetchall()

        if not rows:
            return None

        if user_latitude is None or user_longitude is None:
            return get_poi_by_label_class(label_class)

        def haversine_km(lat1, lon1, lat2, lon2):
            earth_radius_km = 6371.0

            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)

            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)

            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat1_rad)
                * math.cos(lat2_rad)
                * math.sin(dlon / 2) ** 2
            )

            return 2 * earth_radius_km * math.asin(math.sqrt(a))

        best_row = None
        best_distance = float("inf")

        for row in rows:
            distance = haversine_km(
                user_latitude,
                user_longitude,
                row["lat"],
                row["lng"],
            )

            if distance < best_distance:
                best_distance = distance
                best_row = row

        if not best_row:
            return None

        poi = get_poi_by_id(best_row["poi_id"])

        if poi:
            poi["distance_km"] = round(best_distance, 3)

        return poi

    finally:
        conn.close()