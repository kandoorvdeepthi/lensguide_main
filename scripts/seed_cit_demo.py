import sqlite3
from pathlib import Path
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

SOURCE_DB = ROOT / "db" / "PS-06.db"
DEMO_DB = ROOT / "db" / "PS-06_CIT_DEMO.db"


# ============================================================
# DEMO IDS
# ============================================================

CITY_ID = "city_bengaluru_cit"

CIT_POI = "poi_cit_demo"
KFC_POI = "poi_kfc_demo"
TEMPLE_POI = "poi_temple_demo"
CAFE_POI = "poi_cafe_demo"

CIT_SCENE = "scene_cit_demo"

NOW = datetime.now().isoformat(timespec="seconds")


# ============================================================
# DEMO COORDINATES
# ============================================================
# These are DEMO/TEST coordinates for the prototype.
# We will replace the POI coordinates with verified real
# coordinates before presenting them as real-world locations.

CIT_LAT = 13.012338
CIT_LNG = 77.703378

KFC_LAT = 13.011700
KFC_LNG = 77.699800

TEMPLE_LAT = 13.010790
TEMPLE_LNG = 77.705040

CAFE_LAT = 13.013000
CAFE_LNG = 77.704000


# ============================================================
# HELPERS
# ============================================================

def columns(conn, table):
    return [
        row[1]
        for row in conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    ]


def insert_row(conn, table, values):
    cols = columns(conn, table)

    if len(cols) != len(values):
        raise RuntimeError(
            f"{table}: expected {len(cols)} values, "
            f"received {len(values)}"
        )

    placeholders = ",".join(["?"] * len(cols))

    conn.execute(
        f"""
        INSERT OR REPLACE INTO {table}
        ({",".join(cols)})
        VALUES ({placeholders})
        """,
        values,
    )


def distance_km(lat1, lon1, lat2, lon2):
    r = 6371.0

    p1 = radians(lat1)
    p2 = radians(lat2)

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(p1)
        * cos(p2)
        * sin(dlon / 2) ** 2
    )

    return r * 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )


def bearing_deg(lat1, lon1, lat2, lon2):
    p1 = radians(lat1)
    p2 = radians(lat2)

    dlng = radians(lon2 - lon1)

    x = sin(dlng) * cos(p2)

    y = (
        cos(p1) * sin(p2)
        - sin(p1)
        * cos(p2)
        * cos(dlng)
    )

    bearing = atan2(x, y)

    return int(
        (bearing * 180 / 3.141592653589793 + 360) % 360
    )


# ============================================================
# START
# ============================================================

print("=" * 70)
print("SEEDING CIT DEMO DATABASE")
print("=" * 70)

print(f"Demo DB   : {DEMO_DB}")
print(f"Source DB : {SOURCE_DB}")


if not SOURCE_DB.exists():
    raise FileNotFoundError(
        f"Source database not found:\n{SOURCE_DB}"
    )

if not DEMO_DB.exists():
    raise FileNotFoundError(
        f"Demo database not found:\n{DEMO_DB}"
    )


source = sqlite3.connect(SOURCE_DB)
conn = sqlite3.connect(DEMO_DB)

conn.execute("PRAGMA foreign_keys = ON")


try:

    # ========================================================
    # 1. REFERENCE DATA
    # ========================================================

    print("\n[1/8] Copying reference data...")

    # --------------------------------------------------------
    # CURRENCIES
    # --------------------------------------------------------

    currency = source.execute(
        """
        SELECT *
        FROM currencies
        WHERE iso4217 = 'INR'
        LIMIT 1
        """
    ).fetchone()

    if currency is None:
        raise RuntimeError(
            "INR was not found in PS-06.db"
        )

    insert_row(
        conn,
        "currencies",
        currency
    )

    print("  ✓ INR copied")


    # --------------------------------------------------------
    # COUNTRIES
    # --------------------------------------------------------

    country = source.execute(
        """
        SELECT *
        FROM countries
        WHERE iso2 = 'IN'
        LIMIT 1
        """
    ).fetchone()

    if country is None:
        raise RuntimeError(
            "India was not found in PS-06.db"
        )

    insert_row(
        conn,
        "countries",
        country
    )

    country_id = country[0]

    print(
        f"  ✓ India copied: {country_id}"
    )


    # --------------------------------------------------------
    # LANGUAGES
    # --------------------------------------------------------

    languages = source.execute(
        """
        SELECT *
        FROM languages
        WHERE bcp47 IN ('en-IN', 'kn')
        ORDER BY bcp47
        """
    ).fetchall()

    if len(languages) != 2:
        raise RuntimeError(
            "Could not find both en-IN and kn "
            "language records in PS-06.db"
        )

    for language in languages:
        insert_row(
            conn,
            "languages",
            language
        )

    print("  ✓ English (India) copied")
    print("  ✓ Kannada copied")


    # --------------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------------

    categories = source.execute(
        """
        SELECT *
        FROM categories
        """
    ).fetchall()

    for category in categories:
        insert_row(
            conn,
            "categories",
            category
        )

    print(
        f"  ✓ categories copied: {len(categories)}"
    )


    # --------------------------------------------------------
    # IMPORTANT:
    # Commit reference data BEFORE creating dependent rows.
    # --------------------------------------------------------

    conn.commit()

    print("  ✓ reference data committed")


    # --------------------------------------------------------
    # VERIFY FOREIGN-KEY PARENTS
    # --------------------------------------------------------

    country_check = conn.execute(
        """
        SELECT country_id
        FROM countries
        WHERE country_id = ?
        """,
        (country_id,),
    ).fetchone()

    if country_check is None:
        raise RuntimeError(
            f"Country FK missing: {country_id}"
        )


    language_check = conn.execute(
        """
        SELECT bcp47
        FROM languages
        WHERE bcp47 = 'kn'
        """
    ).fetchone()

    if language_check is None:
        raise RuntimeError(
            "Language FK missing: kn"
        )


    currency_check = conn.execute(
        """
        SELECT iso4217
        FROM currencies
        WHERE iso4217 = 'INR'
        """
    ).fetchone()

    if currency_check is None:
        raise RuntimeError(
            "Currency FK missing: INR"
        )


    print("  ✓ foreign-key references verified")


    # ========================================================
    # 2. CITY
    # ========================================================

    print("\n[2/8] Creating Bengaluru city...")


    insert_row(
        conn,
        "cities",
        (
            CITY_ID,
            "Bengaluru",
            "Karnataka",
            country_id,
            "IN",
            12.9716,
            77.5946,
            "Asia/Kolkata",
            "South India",
            8495492,
            "tropical_highland",
            "October-February",
            "kn",
            "Bengaluru city record used for the LensGuide CIT demonstration.",
            "active",
            NOW,
        ),
    )


    conn.commit()

    print("  ✓ Bengaluru created")


    # ========================================================
    # 3. POIs
    # ========================================================

    print("\n[3/8] Creating CIT demo POIs...")


    pois = [

        (
            CIT_POI,
            CITY_ID,
            "Cambridge Institute of Technology",
            "cat_a7ff83bf",
            "heritage",
            CIT_LAT,
            CIT_LNG,
            120,
            "0",
            "INR",
            0.200,
            85,
            90,
            "08:30",
            "16:30",
            "Sunday",
            "Year-round",
            "Campus accessible",
            "cit,college,landmark,campus,technology",
            "Cambridge Institute of Technology demo landmark.",
            1,
            "active",
            NOW,
        ),

        (
            KFC_POI,
            CITY_ID,
            "KFC - CIT Area",
            "cat_7bb74cf2",
            "food",
            KFC_LAT,
            KFC_LNG,
            45,
            "250",
            "INR",
            1.200,
            80,
            70,
            "11:00",
            "23:00",
            "",
            "Year-round",
            "Accessible",
            "restaurant,kfc,food",
            "Demo restaurant POI near the CIT campus.",
            0,
            "active",
            NOW,
        ),

        (
            TEMPLE_POI,
            CITY_ID,
            "Sri Gayathri Temple - Demo",
            "cat_54243992",
            "heritage_temple",
            TEMPLE_LAT,
            TEMPLE_LNG,
            45,
            "0",
            "INR",
            0.050,
            70,
            80,
            "06:00",
            "20:30",
            "",
            "Year-round",
            "Accessible",
            "temple,heritage,religious",
            "Demo temple POI near the CIT campus.",
            0,
            "active",
            NOW,
        ),

        (
            CAFE_POI,
            CITY_ID,
            "CIT Cafe - Demo",
            "cat_7bb74cf2",
            "food",
            CAFE_LAT,
            CAFE_LNG,
            30,
            "100",
            "INR",
            0.300,
            75,
            75,
            "07:30",
            "22:00",
            "",
            "Year-round",
            "Accessible",
            "cafe,tea,food",
            "Demo cafe POI near the CIT campus.",
            0,
            "active",
            NOW,
        ),
    ]


    for poi in pois:

        insert_row(
            conn,
            "activities_poi",
            poi
        )

        print(
            f"  ✓ {poi[2]}"
        )


        # ========================================================
    # CIT LANDMARK RECOGNITION MAPPING
    # ========================================================

    print("  ✓ Creating CIT landmark recognition mapping...")

    insert_row(
        conn,
        "landmark_image_set",
        (
            "img_cit_demo_001",
            CIT_POI,
            "cit_cambridge_institute",
            "demo/cit_cambridge_institute.jpg",
            "demo",
            0,
            0,
            "demo",
            0,
            "demo",
            NOW,
        ),
    )

    print("  ✓ CIT recognition mapping created")

    conn.commit()




    # ========================================================
    # 4. POI FACTS
    # ========================================================

    print("\n[4/8] Creating POI facts...")


    facts = [

        (
            "fact_cit_001",
            CIT_POI,
            "identity",
            "Cambridge Institute of Technology is the main demonstration landmark for the LensGuide CIT dataset.",
            "en-IN",
            "high",
            1,
            None,
            NOW,
        ),

        (
            "fact_cit_002",
            CIT_POI,
            "location",
            "The demonstration landmark is located in the Bengaluru city dataset.",
            "en-IN",
            "high",
            2,
            None,
            NOW,
        ),

        (
            "fact_kfc_001",
            KFC_POI,
            "type",
            "KFC is represented as a nearby restaurant in the CIT demonstration dataset.",
            "en-IN",
            "medium",
            1,
            None,
            NOW,
        ),

        (
            "fact_temple_001",
            TEMPLE_POI,
            "type",
            "This is a demonstration temple POI used for nearby-place testing.",
            "en-IN",
            "medium",
            1,
            None,
            NOW,
        ),

        (
            "fact_cafe_001",
            CAFE_POI,
            "type",
            "This is a demonstration cafe POI used for nearby-place testing.",
            "en-IN",
            "medium",
            1,
            None,
            NOW,
        ),
    ]


    for fact in facts:

        insert_row(
            conn,
            "poi_facts_kb",
            fact
        )


    print(
        f"  ✓ facts created: {len(facts)}"
    )


    conn.commit()


    # ========================================================
    # 5. KNOWLEDGE BASE
    # ========================================================

    print("\n[5/8] Creating knowledge base...")


    knowledge = [

        (
            "kb_cit_001",
            CITY_ID,
            CIT_POI,
            "overview",
            "Cambridge Institute of Technology",
            "Cambridge Institute of Technology is the main demo landmark used for LensGuide testing around the CIT area.",
            "en-IN",
            35,
            "CIT demo dataset",
            None,
            "Year-round",
            NOW,
        ),

        (
            "kb_kfc_001",
            CITY_ID,
            KFC_POI,
            "overview",
            "Nearby Restaurant",
            "KFC is represented as a nearby restaurant POI in the CIT demonstration dataset.",
            "en-IN",
            25,
            "CIT demo dataset",
            None,
            "Year-round",
            NOW,
        ),

        (
            "kb_temple_001",
            CITY_ID,
            TEMPLE_POI,
            "overview",
            "Nearby Temple",
            "A demonstration temple POI used to test nearby-place discovery around CIT.",
            "en-IN",
            25,
            "CIT demo dataset",
            None,
            "Year-round",
            NOW,
        ),

        (
            "kb_cafe_001",
            CITY_ID,
            CAFE_POI,
            "overview",
            "Nearby Cafe",
            "A demonstration cafe POI used to test nearby-place discovery around CIT.",
            "en-IN",
            25,
            "CIT demo dataset",
            None,
            "Year-round",
            NOW,
        ),
    ]


    for item in knowledge:

        insert_row(
            conn,
            "place_kb",
            item
        )


    print(
        f"  ✓ knowledge chunks created: {len(knowledge)}"
    )


    conn.commit()


    # ========================================================
    # 6. TRAVEL MATRIX
    # ========================================================

    print("\n[6/8] Creating travel matrix...")


    locations = {
        CIT_POI: (CIT_LAT, CIT_LNG),
        KFC_POI: (KFC_LAT, KFC_LNG),
        TEMPLE_POI: (TEMPLE_LAT, TEMPLE_LNG),
        CAFE_POI: (CAFE_LAT, CAFE_LNG),
    }


    matrix_count = 0


    for origin_id, (olat, olng) in locations.items():

        for destination_id, (dlat, dlng) in locations.items():

            if origin_id == destination_id:
                continue


            distance = distance_km(
                olat,
                olng,
                dlat,
                dlng,
            )


            # Approximate walking time for DEMO purposes.
            minutes = max(
                1,
                round(distance / 0.075)
            )


            bearing = bearing_deg(
                olat,
                olng,
                dlat,
                dlng,
            )


            matrix_id = (
                f"matrix_{origin_id}_{destination_id}"
            )


            row = (
                matrix_id,
                origin_id,
                destination_id,
                "walking",
                minutes,
                round(distance, 3),
                round(distance * 0.02, 3),
                "0",
                "INR",
                bearing,
                NOW,
            )


            insert_row(
                conn,
                "poi_travel_matrix",
                row
            )


            matrix_count += 1


    conn.commit()


    print(
        f"  ✓ travel matrix rows: {matrix_count}"
    )


    # ========================================================
    # 7. XR SCENE
    # ========================================================

    print("\n[7/8] Creating XR scene...")


    xr_row = (
        CIT_SCENE,
        "poi",
        CIT_POI,
        CITY_ID,
        "CIT Landmark XR Demo",
        "landmark",
        0,
        0,
        20.00,
        0,
        0,
        1,
        None,
        "demo",
        "active",
        NOW,
    )


    insert_row(
        conn,
        "xr_scenes",
        xr_row
    )


    conn.execute(
        """
        UPDATE activities_poi
        SET has_xr_scene = 1,
            updated_at = ?
        WHERE poi_id = ?
        """,
        (
            NOW,
            CIT_POI,
        ),
    )


    conn.commit()


    print("  ✓ CIT XR scene created")


    # ========================================================
    # 8. VERIFY
    # ========================================================

    print("\n[8/8] Verifying seeded data...")


    checks = {

        "countries": """
            SELECT COUNT(*)
            FROM countries
            WHERE country_id = ?
        """,

        "currencies": """
            SELECT COUNT(*)
            FROM currencies
            WHERE iso4217 = 'INR'
        """,

        "languages": """
            SELECT COUNT(*)
            FROM languages
            WHERE bcp47 IN ('en-IN', 'kn')
        """,

        "cities": """
            SELECT COUNT(*)
            FROM cities
            WHERE city_id = ?
        """,

        "pois": """
            SELECT COUNT(*)
            FROM activities_poi
            WHERE city_id = ?
        """,

        "facts": """
            SELECT COUNT(*)
            FROM poi_facts_kb
        """,

        "knowledge": """
            SELECT COUNT(*)
            FROM place_kb
        """,

        "travel": """
            SELECT COUNT(*)
            FROM poi_travel_matrix
        """,

        "xr": """
            SELECT COUNT(*)
            FROM xr_scenes
            WHERE scene_id = ?
        """,
    }


    results = {}


    results["countries"] = conn.execute(
        checks["countries"],
        (country_id,),
    ).fetchone()[0]


    results["currencies"] = conn.execute(
        checks["currencies"]
    ).fetchone()[0]


    results["languages"] = conn.execute(
        checks["languages"]
    ).fetchone()[0]


    results["cities"] = conn.execute(
        checks["cities"],
        (CITY_ID,),
    ).fetchone()[0]


    results["pois"] = conn.execute(
        checks["pois"],
        (CITY_ID,),
    ).fetchone()[0]


    results["facts"] = conn.execute(
        checks["facts"]
    ).fetchone()[0]


    results["knowledge"] = conn.execute(
        checks["knowledge"]
    ).fetchone()[0]


    results["travel"] = conn.execute(
        checks["travel"]
    ).fetchone()[0]


    results["xr"] = conn.execute(
        checks["xr"],
        (CIT_SCENE,),
    ).fetchone()[0]


    for name, count in results.items():

        print(
            f"  ✓ {name:<12}: {count}"
        )


    # --------------------------------------------------------
    # FOREIGN KEY CHECK
    # --------------------------------------------------------

    fk_errors = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()


    if fk_errors:

        print("\nFOREIGN KEY ERRORS:")
        for error in fk_errors:
            print(error)

        raise RuntimeError(
            "Foreign-key verification failed."
        )


    conn.commit()


    # ========================================================
    # SUCCESS
    # ========================================================

    print("\n" + "=" * 70)
    print("CIT DEMO DATABASE CREATED SUCCESSFULLY")
    print("=" * 70)

    print("""
Demo city:
  Bengaluru

Demo POIs:
  1. Cambridge Institute of Technology
  2. KFC - CIT Area
  3. Sri Gayathri Temple - Demo
  4. CIT Cafe - Demo

Created:
  ✓ Reference data
  ✓ Bengaluru city
  ✓ 4 POIs
  ✓ POI facts
  ✓ Knowledge-base entries
  ✓ Walking travel matrix
  ✓ CIT XR scene
  ✓ Foreign-key verification

IMPORTANT:
  The temple/cafe coordinates are DEMO coordinates.
  They are not being represented as verified real-world
  coordinates yet.

Original PS-06.db was NOT modified.
""")


except Exception as e:

    conn.rollback()

    print("\n" + "=" * 70)
    print("SEEDING FAILED — CHANGES ROLLED BACK")
    print("=" * 70)

    print(f"\nERROR: {type(e).__name__}: {e}")

    raise


finally:

    conn.close()
    source.close()