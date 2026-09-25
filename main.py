from flask import Flask, request, jsonify
from flask_cors import CORS

from agents.vision_agent import identify_landmark, classify_ps06_label
from agents.translation_agent import (
    translate_text,
    translate_facts,
    detect_and_translate,
)

from agents.recommendation_agent import get_nearby_places
from agents.language_map import to_bcp47

from database import (
    search_landmark_by_label,
    search_landmark_with_fallback,
    _format_best_time,
    _pick_fun_fact,
    _pick_description,
)

from db.ps06_connection import (
    get_xr_scene,
    get_poi_by_id,
    resolve_poi_by_label_and_location,
    get_facts,
    get_all_label_classes,
)


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
CORS(app)


@app.route("/")
def home():
    return jsonify({"status": "LensGuide is running!"})


def _format_timings(poi):
    """
    Format POI opening hours safely for the result response.
    activities_poi stores opens_at/closes_at as separate columns,
    not a single "timings" field.
    """
    opens_at = poi.get("opens_at")
    closes_at = poi.get("closes_at")

    if not opens_at or not closes_at:
        return "Not available"

    return f"{opens_at} - {closes_at}"


def _format_entry_fee(poi):
    """
    Format the POI entry fee safely for the API response.
    """
    entry_cost = poi.get("entry_cost")
    currency = poi.get("currency")

    if entry_cost is None:
        return "Not available"

    try:
        if float(entry_cost) == 0:
            return "Free"
    except (TypeError, ValueError):
        pass

    if currency:
        return f"{currency} {entry_cost}"

    return str(entry_cost)


def _build_facts_from_poi(poi, language_bcp47):
    _fact_rows = get_facts(poi["poi_id"], language_bcp47)
    _actual_fact_language = (
        _fact_rows[0]["language"] if _fact_rows else "en-IN"
    )

    return {
        "found": True,
        "poi_id": poi["poi_id"],
        "name": poi["name"],
        "location": f"{poi['city_name']}, {poi['country_name']}",
        "city_id": poi["city_id"],
        "timings": _format_timings(poi),
        "entry_fee": _format_entry_fee(poi),
        "entry_cost": poi["entry_cost"],
        "currency": poi["currency"],
        "best_time": _format_best_time(poi),
        "fun_fact": _pick_fun_fact(
            poi["poi_id"],
            language_bcp47,
        ),
        "fact_language": _actual_fact_language,
        "description": _pick_description(
            poi,
            language_bcp47,
        ),
        "poi_category": poi["poi_category"],
        "typical_duration_minutes": poi[
            "typical_duration_minutes"
        ],
        "popularity_score": poi["popularity_score"],
        "accessibility": poi["accessibility"],
        "has_xr_scene": bool(poi["has_xr_scene"]),
        "lat": poi["lat"],
        "lng": poi["lng"],
        "source": "ps06_database",
    }


def _build_landmark_json_response(
    facts,
    language_bcp47,
    raw_language,
):
    nearby = get_nearby_places(
        facts.get("name", ""),
        poi_id=facts.get("poi_id"),
    )

    poi_id = facts.get("poi_id")
    entry_cost = facts.get("entry_cost")
    currency = facts.get("currency")
    poi_category = facts.get("poi_category")
    popularity_score = facts.get("popularity_score")
    typical_duration = facts.get(
        "typical_duration_minutes"
    )
    accessibility = facts.get("accessibility")
    has_xr_scene = facts.get(
        "has_xr_scene",
        False,
    )

    english = {
        "type": "landmark",
        "poi_id": poi_id,
        "name": facts.get(
            "name",
            "Unknown",
        ),
        "location": facts.get(
            "location",
            "Unknown",
        ),
        "timings": facts.get(
            "timings",
            "Not available",
        ),
        "entry_fee": facts.get(
            "entry_fee",
            "Not available",
        ),
        "entry_cost": entry_cost,
        "currency": currency,
        "best_time": facts.get(
            "best_time",
            "Not available",
        ),
        "fun_fact": facts.get(
            "fun_fact",
            "Not available",
        ),
        "description": facts.get(
            "description",
            "",
        ),
        "source": facts.get(
            "source",
            "",
        ),
        "poi_category": poi_category,
        "popularity_score": popularity_score,
        "typical_duration_minutes": typical_duration,
        "accessibility": accessibility,
        "has_xr_scene": has_xr_scene,
        "nearby": nearby.get(
            "nearby",
            {},
        ),
    }

    translated_raw = translate_facts(
        dict(facts),
        raw_language,
    )

    translated = {
        "type": "landmark",
        "poi_id": poi_id,
        "name": translated_raw.get(
            "name",
            english["name"],
        ),
        "location": translated_raw.get(
            "location",
            english["location"],
        ),
        "timings": translated_raw.get(
            "timings",
            english["timings"],
        ),
        "entry_fee": translated_raw.get(
            "entry_fee",
            english["entry_fee"],
        ),
        "entry_cost": entry_cost,
        "currency": currency,
        "best_time": translated_raw.get(
            "best_time",
            english["best_time"],
        ),
        "fun_fact": translated_raw.get(
            "fun_fact",
            english["fun_fact"],
        ),
        "description": translated_raw.get(
            "description",
            english["description"],
        ),
        "source": translated_raw.get(
            "source",
            english["source"],
        ),
        "poi_category": poi_category,
        "popularity_score": popularity_score,
        "typical_duration_minutes": typical_duration,
        "accessibility": accessibility,
        "has_xr_scene": has_xr_scene,
        "nearby": nearby.get(
            "nearby",
            {},
        ),
        "language": language_bcp47,
    }

    return {
        "status": "success",
        "category": "landmark",
        "ps06_matched": True,
        "english": english,
        "translated": translated,
    }


@app.route("/identify", methods=["POST"])
def identify():
    if "file" not in request.files:
        return jsonify({
            "error": "No photo sent"
        }), 400

    file = request.files["file"]
    image_bytes = file.read()

    raw_language = request.form.get(
        "language",
        "English",
    )
    language_bcp47 = to_bcp47(raw_language)

    # GPS coordinates from Flutter
    raw_lat = request.form.get("latitude")
    raw_lng = request.form.get("longitude")

    latitude = None
    longitude = None

    if raw_lat is not None and raw_lng is not None:
        try:
            latitude = float(raw_lat)
            longitude = float(raw_lng)
        except (TypeError, ValueError):
            latitude = None
            longitude = None

    print(
        f"[GPS DEBUG] latitude={latitude}, "
        f"longitude={longitude}"
    )

    # Agent 1 — Vision Agent
    vision_result = identify_landmark(image_bytes)
    landmark_type = vision_result.get(
        "TYPE",
        "unknown",
    )

    # =====================
    # LANDMARK HANDLING
    # =====================
    if landmark_type == "landmark":
        landmark_name = vision_result.get(
            "NAME",
            "",
        )

        # Try PS-06 closed-set match FIRST
        ps06_match = classify_ps06_label(
            image_bytes
        )

        # -----------------------------------------
        # CASE 1: CONFIDENT PS-06 MATCH
        # -----------------------------------------
        if ps06_match["matched"]:
            label_class = ps06_match[
                "label_class"
            ]

            facts = None

            # Prefer GPS-aware canonical POI resolution
            if (
                latitude is not None
                and longitude is not None
            ):
                located = (
                    resolve_poi_by_label_and_location(
                        label_class,
                        latitude,
                        longitude,
                    )
                )

                if located:
                    poi = get_poi_by_id(
                        located["poi_id"]
                    )

                    if poi:
                        print(
                            f"[PS-06] Closed-set match "
                            f"'{label_class}' resolved by "
                            f"location to "
                            f"{poi['poi_id']} "
                            f"({located['distance_km']} km away)"
                        )

                        facts = _build_facts_from_poi(
                            poi,
                            language_bcp47,
                        )

            # Fallback if GPS unavailable
            # or resolution failed
            if facts is None:
                print(
                    f"[PS-06] Closed-set match: "
                    f"{label_class} "
                    f"(no GPS or resolution failed)"
                )

                facts = search_landmark_by_label(
                    label_class,
                    language_bcp47,
                )

            return jsonify(
                _build_landmark_json_response(
                    facts,
                    language_bcp47,
                    raw_language,
                )
            )

        # -----------------------------------------
        # CASE 2: BELOW CONFIDENCE THRESHOLD
        # -----------------------------------------
        elif ps06_match.get(
            "requires_selection"
        ):
            print(
                f"[PS-06] Ambiguous match, "
                f"{len(ps06_match.get('candidates', []))} "
                f"candidates - asking user"
            )

            return jsonify({
                "status": "selection_required",
                "category": "landmark",
                "ps06_matched": False,
                "requires_selection": True,
                "candidates": ps06_match.get(
                    "candidates",
                    [],
                ),
            })

        # -----------------------------------------
        # CASE 3: NO PLAUSIBLE PS-06 MATCH
        # -----------------------------------------
        else:
            print(
                f"[PS-06] No closed-set match, "
                f"using open-world name: "
                f"{landmark_name}"
            )

            facts = search_landmark_with_fallback(
                landmark_name,
                language_bcp47,
            )

            return jsonify(
                _build_landmark_json_response(
                    facts,
                    language_bcp47,
                    raw_language,
                )
            )

    # =====================
    # SIGN/MENU HANDLING
    # =====================
    elif landmark_type == "text":
        detected_text = vision_result.get(
            "CONTENT",
            "",
        )

        detected_language = vision_result.get(
            "LANGUAGE",
            "Unknown",
        )

        translation_result = detect_and_translate(
            detected_text,
            raw_language,
        )

        is_safety_critical_guess = any(
            keyword in detected_text.lower()
            for keyword in [
                "allerg",
                "peanut",
                "nut",
                "seafood",
                "shellfish",
                "gluten",
            ]
        )

        english = {
            "type": "text",
            "detected_language": detected_language,
            "original_text": detected_text,
            "translated_text": translation_result.get(
                "translation",
                "",
            ),
            "target_language": raw_language,
            "is_safety_critical": (
                is_safety_critical_guess
            ),
        }

        translated = {
            "type": "text",
            "detected_language": detected_language,
            "original_text": detected_text,
            "translated_text": translation_result.get(
                "translation",
                "",
            ),
            "target_language": raw_language,
            "is_safety_critical": (
                is_safety_critical_guess
            ),
            "language": language_bcp47,
        }

        return jsonify({
            "status": "success",
            "category": "menu_or_sign",
            "english": english,
            "translated": translated,
        })

    # =====================
    # UNKNOWN HANDLING
    # =====================
    else:
        return jsonify({
            "status": "not_identified",
            "category": "unknown",
            "message": "Could not identify the image",
            "english": {
                "type": "unknown",
                "message": (
                    "Please try with a clearer photo"
                ),
            },
            "translated": {
                "type": "unknown",
                "message": (
                    "Please try with a clearer photo"
                ),
                "language": language_bcp47,
            },
        })


@app.route("/identify/select", methods=["POST"])
def identify_select():
    """
    Handles the user's choice after a "selection_required" response.
    Reuses the exact same GPS-aware resolution and response-building
    logic as /identify's matched case - no duplicated fact-generation.
    """
    data = request.get_json()

    if not data or "label_class" not in data:
        return jsonify({
            "error": "label_class required"
        }), 400

    label_class = data["label_class"]
    raw_language = data.get("language", "English")
    language_bcp47 = to_bcp47(raw_language)
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    poi = None

    if latitude is not None and longitude is not None:
        located = resolve_poi_by_label_and_location(
            label_class,
            float(latitude),
            float(longitude),
        )
        if located:
            poi = get_poi_by_id(located["poi_id"])

    if poi is not None:
        facts = _build_facts_from_poi(poi, language_bcp47)
    else:
        facts = search_landmark_by_label(label_class, language_bcp47)
        if not facts.get("found"):
            return jsonify({
                "status": "not_recognized",
                "category": "landmark",
                "message": "Could not resolve the selected candidate.",
            })

    return jsonify(
        _build_landmark_json_response(
            facts,
            language_bcp47,
            raw_language,
        )
    )


@app.route("/select-candidate", methods=["POST"])
def select_candidate():
    """
    Second half of the confidence-gate flow. The user has already
    explicitly chosen one label_class from a "selection_required"
    response - Gemini is NOT called again here. We validate the
    choice against the real PS-06 closed-set, then ground it
    directly using the same GPS-aware resolution + response
    builders already used by /identify's confident-match case.
    """
    data = request.get_json()

    if not data or "label_class" not in data:
        return jsonify({"error": "label_class required"}), 400

    label_class = data["label_class"]

    # Never trust an arbitrary client-supplied string - validate
    # against the real, current PS-06 closed-set.
    valid_classes = {c["label_class"] for c in get_all_label_classes()}
    if label_class not in valid_classes:
        return jsonify({"error": f"Unknown label_class: {label_class}"}), 400

    raw_language = data.get("language", "English")
    language_bcp47 = to_bcp47(raw_language)
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    poi = None

    if latitude is not None and longitude is not None:
        try:
            located = resolve_poi_by_label_and_location(
                label_class, float(latitude), float(longitude)
            )
        except (TypeError, ValueError):
            located = None

        if located:
            poi = get_poi_by_id(located["poi_id"])

    if poi is not None:
        facts = _build_facts_from_poi(poi, language_bcp47)
    else:
        # No GPS, or GPS resolution failed - fall back to the
        # existing popularity-based match, same as /identify does.
        facts = search_landmark_by_label(label_class, language_bcp47)

        if not facts.get("found"):
            return jsonify({
                "status": "not_recognized",
                "category": "landmark",
                "message": "Could not resolve the selected candidate.",
            }), 404

    return jsonify(
        _build_landmark_json_response(facts, language_bcp47, raw_language)
    )


@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({
            "error": "No text provided"
        }), 400

    text = data["text"]

    target_language = data.get(
        "language",
        "English",
    )

    result = translate_text(
        text,
        target_language,
    )

    return jsonify(result)


@app.route("/translate-image", methods=["POST"])
def translate_image():
    """
    Standalone sign/menu image translation. Does NOT touch PS-06,
    does NOT call the landmark/nearby-POI flow, does NOT use
    /identify's response shape - purely reuses the same vision +
    translation functions /identify already calls internally.
    """
    print("[TRANSLATE IMAGE] request received")

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "source_text": "",
            "translated_text": "",
            "message": "No image provided",
        }), 400

    file = request.files["file"]
    image_bytes = file.read()

    target_language = request.form.get("target_language", "English")
    if target_language not in ("English", "Hindi", "Tamil"):
        target_language = "English"

    # Reuse the existing vision agent exactly as /identify does.
    vision_result = identify_landmark(image_bytes)
    landmark_type = vision_result.get("TYPE", "unknown")

    if landmark_type != "text":
        print(f"[TRANSLATE IMAGE] OCR result: TYPE={landmark_type} (not text)")
        return jsonify({
            "success": False,
            "source_text": "",
            "translated_text": "",
            "message": "No readable text found in the image.",
        })

    source_text = vision_result.get("CONTENT", "").strip()
    print(f"[TRANSLATE IMAGE] OCR result: {len(source_text)} chars — {source_text[:80]!r}...")

    if not source_text:
        return jsonify({
            "success": False,
            "source_text": "",
            "translated_text": "",
            "message": "No readable text found in the image.",
        })

    # Reuse the existing translation function exactly as /identify does.
    translation_result = detect_and_translate(source_text, target_language)
    translated_text = translation_result.get("translation", "").strip()
    print(f"[TRANSLATE IMAGE] translated result: {len(translated_text)} chars — {translated_text[:80]!r}...")

    if not translation_result.get("success") or not translated_text:
        return jsonify({
            "success": False,
            "source_text": source_text,
            "translated_text": "",
            "message": "No readable text found in the image.",
        })

    response_body = {
        "success": True,
        "source_text": source_text,
        "translated_text": translated_text,
        "target_language": target_language,
    }
    print("[TRANSLATE IMAGE] response sent")
    return jsonify(response_body)


@app.route("/xr_scene", methods=["GET"])
def xr_scene():
    poi_id = request.args.get(
        "poi_id"
    )

    if not poi_id:
        return jsonify({
            "error": "poi_id query param required",
        }), 400

    scene = get_xr_scene(poi_id)

    if not scene:
        return jsonify({
            "found": False,
            "message": (
                "No AR-placeable scene for this POI"
            ),
        })

    return jsonify({
        "found": True,
        "scene_id": scene["scene_id"],
        "scene_type": scene["scene_type"],
        "name": scene["name"],
        "real_scale_metres": scene[
            "real_scale_metres"
        ],
        "supports_webxr": bool(
            scene["supports_webxr"]
        ),
        "supports_ar_placement": bool(
            scene["supports_ar_placement"]
        ),
        "total_bytes": scene["total_bytes"],
    })


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8000,
    )
