from flask import Flask, request, jsonify
from flask_cors import CORS
from agents.vision_agent import identify_landmark
from agents.translation_agent import translate_text, detect_and_translate
from agents.recommendation_agent import get_nearby_places
from database import search_landmark_with_fallback

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

@app.route("/")
def home():
    return jsonify({"status": "LensGuide is running!"})

@app.route("/identify", methods=["POST"])
def identify():
    if "file" not in request.files:
        return jsonify({"error": "No photo sent"}), 400

    file = request.files["file"]
    image_bytes = file.read()
    language = request.form.get("language", "English")

    # Agent 1 — Vision Agent
    vision_result = identify_landmark(image_bytes)
    landmark_type = vision_result.get("TYPE", "unknown")

    # =====================
    # LANDMARK HANDLING
    # =====================
    if landmark_type == "landmark":
        landmark_name = vision_result.get("NAME", "")
        location = vision_result.get("LOCATION", "Unknown")

        # Agent 2 — RAG + Wikipedia
        facts = search_landmark_with_fallback(landmark_name)

        # Agent 4 — Nearby Recommendations
        nearby = get_nearby_places(landmark_name)

        # Build English response
        english = {
            "type": "landmark",
            "name": landmark_name,
            "location": location,
            "timings": facts.get("timings", "Not available"),
            "entry_fee": facts.get("entry_fee", "Not available"),
            "best_time": facts.get("best_time", "Not available"),
            "fun_fact": facts.get("fun_fact", "Not available"),
            "description": facts.get("description", ""),
            "source": facts.get("source", ""),
            "nearby": nearby.get("nearby", {})
        }

        # Agent 3 — Translation
        if language.lower() == "english":
            translated = english.copy()
            translated["language"] = "english"
        else:
            def t(text):
                if not text or text == "Not available":
                    return text
                result = translate_text(text, language)
                return result["translated_text"] if result["success"] else text

            translated = {
                "type": t("landmark"),
                "name": t(landmark_name),
                "location": t(location),
                "timings": t(facts.get("timings", "Not available")),
                "entry_fee": t(facts.get("entry_fee", "Not available")),
                "best_time": t(facts.get("best_time", "Not available")),
                "fun_fact": t(facts.get("fun_fact", "Not available")),
                "description": t(facts.get("description", "")),
                "source": t(facts.get("source", "")),
                "nearby": nearby.get("nearby", {}),
                "language": language
            }

        return jsonify({
            "status": "success",
            "category": "landmark",
            "english": english,
            "translated": translated
        })

    # =====================
    # SIGN/MENU HANDLING
    # =====================
    elif landmark_type == "text":
        detected_text = vision_result.get("CONTENT", "")
        detected_language = vision_result.get("LANGUAGE", "Unknown")

        translation_result = detect_and_translate(detected_text, language)

        english = {
            "type": "text",
            "detected_language": detected_language,
            "original_text": detected_text,
            "translated_text": translation_result.get("translation", ""),
            "target_language": language
        }

        if language.lower() == "english":
            translated = english.copy()
            translated["language"] = "english"
        else:
            def t(text):
                if not text:
                    return text
                result = translate_text(text, language)
                return result["translated_text"] if result["success"] else text

            translated = {
                "type": t("text"),
                "detected_language": t(detected_language),
                "original_text": detected_text,
                "translated_text": translation_result.get("translation", ""),
                "target_language": t(language),
                "language": language
            }

        return jsonify({
            "status": "success",
            "category": "menu_or_sign",
            "english": english,
            "translated": translated
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
                "message": "Please try with a clearer photo"
            },
            "translated": {
                "type": "unknown",
                "message": "Please try with a clearer photo",
                "language": language
            }
        })


@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400
    text = data["text"]
    target_language = data.get("language", "English")
    result = translate_text(text, target_language)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=8000)