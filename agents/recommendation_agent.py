"""
recommendation_agent.py — PS-06 migration (Step 3)

This module used to return a hardcoded dict of hotels/restaurants/
attractions, with OpenStreetMap Overpass as a live-data attempt.

It now queries PS-06.db's poi_travel_matrix (6,418 real rows),
which gives exact minutes and distance_km for each transport mode
between any two POIs in the dataset — no external API call needed.
"""

from decimal import Decimal
from db.ps06_connection import get_nearby, search_poi_by_name


def _format_cost(cost_text: str, currency: str) -> str:
    amount = Decimal(cost_text)  # never float()
    if amount == Decimal("0.00"):
        return "Free"
    return f"{amount} {currency}"


def _format_distance(distance_km) -> str:
    # distance_km comes back from SQLite REAL affinity as a float —
    # safe here because it's display-only, never re-added or compared.
    return f"{distance_km:.1f} km"

def _format_timings(opens_at, closes_at):
    if not opens_at or not closes_at:
        return "Not available"
    return f"{opens_at} - {closes_at}"


def _place_dict(row: dict) -> dict:
    return {
        "poi_id": row["dest_poi_id"],
        "name": row["dest_name"],
        "poi_category": row["poi_category"],
        "distance": _format_distance(row["distance_km"]),
        "distance_km": row["distance_km"],
        "minutes": row["minutes"],
        "mode": row["mode"],
        "cost": _format_cost(row["cost"], row["currency"]),
        "popularity_score": row["popularity_score"],
        "entry_fee": _format_cost(row["entry_cost"], row["dest_currency"]),
        "timings": _format_timings(row.get("opens_at"), row.get("closes_at")),
        "description": row.get("description", ""),
        "lat": row["lat"],
        "lng": row["lng"],
    }


def get_nearby_places_ps06(poi_id: str, mode: str = "walking", limit: int = 3) -> dict:
    """
    Core PS-06 lookup, starting from a known poi_id. Splits
    poi_travel_matrix results into the existing hotels/restaurants/
    attractions buckets so main.py's response shape is unchanged.
    """
    rows = get_nearby(poi_id, mode=mode, limit=limit)

    hotels = []
    restaurants = []
    attractions = []

    for row in rows:
        place = _place_dict(row)
        if row["poi_category"] == "food":
            restaurants.append(place)
        else:
            attractions.append(place)

    return {
        "found": bool(rows),
        "source": "ps06_travel_matrix",
        "nearby": {
            "hotels": hotels,
            "restaurants": restaurants,
            "attractions": attractions,
        },
    }


def get_nearby_places(landmark_name: str, latitude: float = None, longitude: float = None, poi_id: str = None) -> dict:
    """
    PUBLIC ENTRY POINT — signature extended with an optional poi_id.

    When poi_id is supplied (the normal case now that identification
    already resolves one), it's used directly — no name lookup needed.
    When poi_id is absent, falls back to the existing name-match
    behavior exactly as before, so nothing that already calls this
    function without poi_id breaks.
    """
    try:
        if poi_id:
            return get_nearby_places_ps06(poi_id)

        poi = search_poi_by_name(landmark_name)

        if not poi:
            print(f"[PS-06] No POI found for nearby lookup: {landmark_name}")
            return {
                "found": False,
                "source": "ps06_travel_matrix",
                "nearby": {"hotels": [], "restaurants": [], "attractions": []},
            }

        return get_nearby_places_ps06(poi["poi_id"])

    except Exception as e:
        print("[PS-06] Nearby places error:", str(e))
        return {
            "found": False,
            "source": "ps06_travel_matrix",
            "nearby": {"hotels": [], "restaurants": [], "attractions": []},
        }
