"""
database.py — PS-06 migration

This module queries PS-06.db instead of the old ChromaDB setup.

PS-06 closed-set landmark lookup is preferred when the vision agent
returns a valid label_class.

When GPS coordinates are available, the lookup uses the nearest
matching POI for that label_class.

When GPS is unavailable, it falls back to the deterministic
label_class lookup.
"""

from decimal import Decimal

from agents.language_map import to_bcp47

from db.ps06_connection import (
    search_poi_by_name,
    get_poi_by_label_class,
    get_facts,
    get_place_kb,
    resolve_poi_by_label_and_location,
)


# ============================================================
# FORMATTING HELPERS
# ============================================================

def _format_timings(poi: dict) -> str:
    opens = poi.get("opens_at")
    closes = poi.get("closes_at")

    if not opens or not closes:
        return "Not available"

    return f"{opens} - {closes}"


def _format_entry_fee(poi: dict) -> str:
    """
    PS-06 money is stored as an exact amount + currency pair.

    We use Decimal instead of float so the original monetary
    precision is preserved.
    """
    amount_text = poi.get("entry_cost")
    currency = poi.get("currency")

    if amount_text is None or currency is None:
        return "Not available"

    amount = Decimal(str(amount_text))

    if amount == Decimal("0.00"):
        return "Free"

    return f"{amount} {currency}"


def _format_best_time(poi: dict) -> str:
    season = poi.get("best_season")

    if not season:
        return "Not available"

    return season.replace("_", " ").title()


def _pick_fun_fact(
    poi_id: str,
    language: str = "en-IN",
) -> str:
    """
    Pick the highest-priority fact from the PS-06 knowledge base.
    """
    facts = get_facts(poi_id, language)

    if not facts:
        return "Not available"

    return facts[0]["fact_text"]


def _pick_description(
    poi: dict,
    language: str = "en-IN",
) -> str:
    """
    Prefer PS-06 history/culture knowledge-base content.

    Fall back to the POI's own description if no matching
    knowledge-base content exists.
    """
    kb_rows = get_place_kb(
        poi_id=poi["poi_id"],
        language=language,
    )

    for section in ("history", "culture"):
        for row in kb_rows:
            if row["section"] == section:
                return row["body"]

    return poi.get("description", "")


def _resolve_fact_language(poi_id, requested_bcp47):
    """
    get_facts() falls back to en-IN internally when the requested
    language has no rows. Reports the TRUE language of whatever
    was returned, instead of assuming non-empty == requested.
    """
    rows = get_facts(poi_id, requested_bcp47)

    if not rows:
        return "en-IN"

    return rows[0]["language"]


# ============================================================
# FREE-TEXT LANDMARK SEARCH
# ============================================================

def search_landmark(
    landmark_name: str,
    language: str = "en-IN",
) -> dict:
    """
    Search PS-06 by a free-text landmark name.

    This is mainly used for open-world identification and fallback.
    """
    try:
        poi = search_poi_by_name(landmark_name)

        if not poi:
            return {
                "found": False,
                "message": "Landmark not in PS-06 database",
            }

        print(
            f"[PS-06] Found in database: "
            f"{poi['name']} ({poi['poi_id']})"
        )

        bcp47 = to_bcp47(language)

        return {
            "found": True,
            "poi_id": poi["poi_id"],
            "name": poi["name"],
            "location": (
                f"{poi['city_name']}, "
                f"{poi['country_name']}"
            ),
            "city_id": poi["city_id"],
            "timings": _format_timings(poi),
            "entry_fee": _format_entry_fee(poi),
            "entry_cost": poi["entry_cost"],
            "currency": poi["currency"],
            "best_time": _format_best_time(poi),
            "fun_fact": _pick_fun_fact(
                poi["poi_id"],
                bcp47,
            ),
            "fact_language": _resolve_fact_language(
                poi["poi_id"],
                bcp47,
            ),
            "description": _pick_description(
                poi,
                bcp47,
            ),
            "poi_category": poi["poi_category"],
            "typical_duration_minutes": (
                poi["typical_duration_minutes"]
            ),
            "popularity_score": poi["popularity_score"],
            "accessibility": poi["accessibility"],
            "has_xr_scene": bool(
                poi["has_xr_scene"]
            ),
            "lat": poi["lat"],
            "lng": poi["lng"],
        }

    except Exception as e:
        print("[PS-06] Database error:", str(e))

        return {
            "found": False,
            "message": str(e),
        }


# ============================================================
# CLOSED-SET LABEL SEARCH
# ============================================================

def search_landmark_by_label(
    label_class: str,
    language: str = "en-IN",
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """
    Search PS-06 using the closed-set label_class returned
    by the vision agent.

    If GPS is available:
        Use resolve_poi_by_label_and_location() to choose the
        nearest POI matching the label_class.

    If GPS is unavailable:
        Fall back to get_poi_by_label_class().

    This is important because the same label_class can exist
    in multiple cities.

    Example:
        watchtower_terrace

    exists in multiple PS-06 POIs, so GPS helps choose the
    correct one.
    """

    try:
        poi = None

        # ----------------------------------------------------
        # GPS-AWARE LOOKUP
        # ----------------------------------------------------
        if latitude is not None and longitude is not None:
            print(
                f"[PS-06] GPS-aware lookup for "
                f"'{label_class}'"
            )

            print(
                f"[PS-06] User location: "
                f"{latitude}, {longitude}"
            )

            poi = resolve_poi_by_label_and_location(
                label_class,
                latitude,
                longitude,
            )

            if poi:
                print(
                    f"[PS-06] GPS match: "
                    f"{poi['name']} "
                    f"({poi['poi_id']})"
                )

                if poi.get("distance_km") is not None:
                    print(
                        f"[PS-06] Distance: "
                        f"{poi['distance_km']} km"
                    )

        # ----------------------------------------------------
        # FALLBACK WITHOUT GPS
        # ----------------------------------------------------
        if poi is None:
            print(
                f"[PS-06] No GPS match. "
                f"Using label_class fallback: "
                f"{label_class}"
            )

            poi = get_poi_by_label_class(
                label_class
            )

        # ----------------------------------------------------
        # NOTHING FOUND
        # ----------------------------------------------------
        if not poi:
            return {
                "found": False,
                "message": (
                    f"No POI found for label_class "
                    f"'{label_class}'"
                ),
            }

        # ----------------------------------------------------
        # LANGUAGE
        # ----------------------------------------------------
        bcp47 = to_bcp47(language)

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------
        result = {
            "found": True,
            "poi_id": poi["poi_id"],
            "name": poi["name"],
            "location": (
                f"{poi['city_name']}, "
                f"{poi['country_name']}"
            ),
            "city_id": poi["city_id"],
            "timings": _format_timings(poi),
            "entry_fee": _format_entry_fee(poi),
            "entry_cost": poi["entry_cost"],
            "currency": poi["currency"],
            "best_time": _format_best_time(poi),
            "fun_fact": _pick_fun_fact(
                poi["poi_id"],
                bcp47,
            ),
            "fact_language": _resolve_fact_language(
                poi["poi_id"],
                bcp47,
            ),
            "description": _pick_description(
                poi,
                bcp47,
            ),
            "poi_category": poi["poi_category"],
            "typical_duration_minutes": (
                poi["typical_duration_minutes"]
            ),
            "popularity_score": poi["popularity_score"],
            "accessibility": poi["accessibility"],
            "has_xr_scene": bool(
                poi["has_xr_scene"]
            ),
            "lat": poi["lat"],
            "lng": poi["lng"],
        }

        # Include distance when GPS resolver supplied it.
        if poi.get("distance_km") is not None:
            result["distance_km"] = poi["distance_km"]

        return result

    except Exception as e:
        print(
            "[PS-06] Database error:",
            str(e),
        )

        return {
            "found": False,
            "message": str(e),
        }


# ============================================================
# OPEN-WORLD + PS-06 FALLBACK
# ============================================================

def search_landmark_with_fallback(
    landmark_name: str,
    language: str = "en-IN",
) -> dict:
    """
    First search PS-06 by landmark name.

    If the landmark is not present in PS-06,
    use Wikipedia as the open-world fallback.
    """

    result = search_landmark(
        landmark_name,
        language,
    )

    if result["found"]:
        result["source"] = "ps06_database"
        return result

    print(
        f"[PS-06] Not in database, "
        f"trying Wikipedia for: {landmark_name}"
    )

    from agents.wikipedia_agent import get_wikipedia_facts

    wiki_result = get_wikipedia_facts(
        landmark_name
    )

    return wiki_result
