# test_ps06.py — delete after confirming it works

from db.ps06_connection import (
    get_poi_by_label_class,
    search_poi_by_name,
    get_facts,
    get_place_kb,
    get_nearby,
    get_xr_scene,
    format_money,
)

# Test 1 — find a real POI by name (bridge method)
poi = search_poi_by_name("Jaipur Bazaar")
print("POI:", poi)

if poi:
    poi_id = poi["poi_id"]

    # Test 2 — facts in English
    facts = get_facts(poi_id, "en-IN")
    print("\nFacts (en-IN):", facts)

    # Test 3 — facts in Hindi (may fall back to en-IN)
    facts_hi = get_facts(poi_id, "hi")
    print("\nFacts (hi):", facts_hi)

    # Test 4 — place_kb
    kb = get_place_kb(poi_id=poi_id, language="en-IN")
    print("\nPlace KB:", kb)

    # Test 5 — nearby
    nearby = get_nearby(poi_id, mode="walk")
    print("\nNearby:", nearby)

    # Test 6 — XR scene
    xr = get_xr_scene(poi_id)
    print("\nXR Scene:", xr)

    # Test 7 — money formatting
    money = format_money(poi["entry_cost"], poi["currency"])
    print("\nMoney:", money)
