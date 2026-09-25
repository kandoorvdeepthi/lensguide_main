from google import genai
import os
import time
from PIL import Image
import io
from dotenv import load_dotenv
from db.ps06_connection import get_all_label_classes

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

PS06_CONFIDENCE_THRESHOLD = 0.75

_CONFIDENCE_SCORE_MAP = {
    "high": 0.90,
    "medium": 0.65,
    "low": 0.30,
}

# Fields identify_landmark() can return, across all three of its
# reply shapes (landmark / text / unknown). Used only by the
# multi-line-aware parser below - classify_ps06_label() has its own
# separate, single-line-safe parsing and is untouched.
_IDENTIFY_KNOWN_FIELDS = ("TYPE", "NAME", "LOCATION", "CONTENT", "LANGUAGE", "MESSAGE")


def _parse_structured_reply(result: str) -> dict:
    """
    Parses Gemini's TYPE/NAME/LOCATION or TYPE/CONTENT/LANGUAGE or
    TYPE/MESSAGE reply. Unlike a naive "one field per line" split,
    this correctly handles a field whose value spans MULTIPLE lines
    (e.g. a full multi-line menu under CONTENT) by appending any
    line that doesn't start a new known field to the current field's
    value, rather than silently dropping it.
    """
    lines = result.strip().split("\n")
    parsed = {}
    current_key = None

    for raw_line in lines:
        line = raw_line.rstrip()
        matched_key = None
        value = None

        if ":" in line:
            possible_key, _, rest = line.partition(":")
            possible_key_stripped = possible_key.strip()
            if possible_key_stripped in _IDENTIFY_KNOWN_FIELDS:
                matched_key = possible_key_stripped
                value = rest.strip()

        if matched_key:
            parsed[matched_key] = value
            current_key = matched_key
        elif current_key is not None and line.strip():
            # Continuation line for the current field (e.g. the next
            # menu item) - append rather than discard.
            existing = parsed.get(current_key, "")
            parsed[current_key] = f"{existing}\n{line.strip()}" if existing else line.strip()
        # else: stray blank/pre-field line - ignore

    return parsed


def _generate_with_resilience(prompt, image):
    """
    Retry/fallback wrapper for transient Gemini 503 errors, used by
    both classify_ps06_label() and identify_landmark(). Falls back
    to gemini-2.5-flash (confirmed available on this account) after
    one retry.
    """
    models_to_try = [
    "gemini-3.6-flash",
    "gemini-3.8-flash"
    ]
    last_error = None
    for i, model_name in enumerate(models_to_try):
        try:
            if i == 1:
                time.sleep(1)
            return client.models.generate_content(
                model=model_name,
                contents=[prompt, image]
            )
        except Exception as e:
            last_error = e
            print(f"[PS-06 classifier] attempt {i + 1} with {model_name} failed: {e}")
            continue
    raise last_error


def classify_ps06_label(image_bytes: bytes) -> dict:
    """
    Confidence-gated PS-06 classification with top-3 candidates.
    UNCHANGED from before this fix - own separate, single-line-safe
    parsing (RANK1_LABEL_CLASS etc. are never multi-line, so no
    change is needed here).
    """
    try:
        classes = get_all_label_classes()

        class_lines = "\n".join(
            f"- {c['label_class']}  "
            f"(e.g. {c['name']}, {c['city_name']}, category: {c['poi_category']}. "
            f"{c['description']})"
            for c in classes
        )

        image = Image.open(io.BytesIO(image_bytes))

        prompt = f"""You are matching a travel photo against a CLOSED list
of recognition classes from a synthetic demo dataset. These are
GENERIC place types (e.g. "hot springs", "watchtower terrace",
"spice market walk") - not necessarily real famous landmarks.

Look at the photo carefully. Rank up to 3 classes from the list
below that plausibly match the GENERAL TYPE of place shown, most
confident first. For each rank, state how confident you are. If
fewer than 3 classes plausibly match, use "none" for the
remaining ranks. If the photo is clearly a specific, real-world
famous landmark, or nothing on the list plausibly matches at all,
use "none" for ALL THREE ranks.

Classes:
{class_lines}

Reply EXACTLY in this format, nothing else:
RANK1_LABEL_CLASS: [exact class name from the list above, or none]
RANK1_CONFIDENCE: high, medium, or low
RANK2_LABEL_CLASS: [exact class name from the list above, or none]
RANK2_CONFIDENCE: high, medium, or low
RANK3_LABEL_CLASS: [exact class name from the list above, or none]
RANK3_CONFIDENCE: high, medium, or low"""

        response = _generate_with_resilience(prompt, image)

        result = response.text.strip()
        print("PS-06 classification says:", result)

        lines = result.split("\n")
        parsed = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                parsed[key.strip()] = value.strip()

        valid_classes = {c["label_class"] for c in classes}

        candidates = []
        seen = set()
        for rank in (1, 2, 3):
            lc = parsed.get(f"RANK{rank}_LABEL_CLASS", "none").strip()
            conf_word = parsed.get(f"RANK{rank}_CONFIDENCE", "low").strip().lower()

            if lc == "none" or lc not in valid_classes or lc in seen:
                continue

            seen.add(lc)
            score = _CONFIDENCE_SCORE_MAP.get(conf_word, 0.30)
            candidates.append({
                "label_class": lc,
                "confidence": conf_word,
                "confidence_score": score,
            })

        candidates.sort(key=lambda c: c["confidence_score"], reverse=True)

        if not candidates:
            return {
                "matched": False,
                "requires_selection": False,
                "candidates": [],
                "not_recognized": True,
            }

        top = candidates[0]

        if top["confidence_score"] >= PS06_CONFIDENCE_THRESHOLD:
            return {
                "matched": True,
                "label_class": top["label_class"],
                "confidence": top["confidence"],
                "confidence_score": top["confidence_score"],
                "requires_selection": False,
                "not_recognized": False,
            }

        return {
            "matched": False,
            "requires_selection": True,
            "candidates": [
                {"label_class": c["label_class"], "confidence_score": c["confidence_score"]}
                for c in candidates[:3]
            ],
            "not_recognized": False,
        }

    except Exception as e:
        print("PS-06 classification error:", str(e))
        return {
            "matched": False,
            "requires_selection": False,
            "candidates": [],
            "not_recognized": False,
        }


def identify_landmark(image_bytes: bytes) -> dict:
    """
    Open-world identification. FIXED: now uses _parse_structured_reply
    instead of a naive one-field-per-line split, so multi-line CONTENT
    (e.g. a full menu) is captured completely instead of truncated to
    its first line. Prompt, reply format, and error handling are
    otherwise unchanged.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        prompt = """You are a travel assistant.
        Look at this image carefully.
        
        If you see a landmark reply EXACTLY:
        TYPE: landmark
        NAME: [landmark name]
        LOCATION: [city, country]
        
        If you see a sign or menu reply EXACTLY:
        TYPE: text
        CONTENT: [copy ALL text you see word by word]
        LANGUAGE: [language of the text]
        
        If unknown reply EXACTLY:
        TYPE: unknown
        MESSAGE: Cannot identify"""

        response = _generate_with_resilience(prompt, image)

        result = response.text
        print("Gemini says:", result)

        parsed = _parse_structured_reply(result)

        return parsed

    except Exception as e:
        print("ERROR in vision agent:", str(e))
        return {"TYPE": "error", "MESSAGE": str(e)}