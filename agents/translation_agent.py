from google import genai
import os
import json
from dotenv import load_dotenv
from agents.language_map import to_bcp47, to_display_name, is_english

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def translate_text(text: str, target_language: str = "English") -> dict:
    """
    Translates general free-text content using Gemini.
    Accepts either a display language name or supported BCP-47 tag.
    """
    try:
        prompt_language = target_language

        if target_language in ("hi", "ta", "en-IN"):
            prompt_language = to_display_name(target_language)

        print(f"Translating to {prompt_language}...")

        prompt = f"""Translate the following text to {prompt_language}.

Return ONLY the translated text.
Nothing else. No explanations.

Text to translate:
{text}"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        translated = response.text.strip()

        return {
            "success": True,
            "original_text": text,
            "translated_text": translated,
            "target_language": prompt_language,
        }

    except Exception as e:
        print(f"Translation error: {str(e)}")

        return {
            "success": False,
            "error": str(e)
        }


def translate_facts(facts: dict, target_language: str = "English") -> dict:
    """
    Translates genuine free-text PS-06 fields.

    Structured/numeric fields such as timings, entry fees,
    coordinates, POI IDs, categories and scores are not translated.
    """
    try:
        bcp47 = to_bcp47(target_language)

        # English requires no translation.
        if is_english(bcp47):
            return facts

        # If PS-06 already contains facts in the requested language,
        # avoid another Gemini call.
        already_native = facts.get("fact_language") == bcp47

        if already_native:
            print(f"Facts already in {bcp47} from PS-06 — skipping Gemini")
            facts["language"] = bcp47
            return facts

        print(f"Translating facts to {bcp47} via Gemini...")

        display_lang = to_display_name(bcp47)

        if "description" in facts and facts["description"]:
            result = translate_text(
                facts["description"],
                display_lang
            )

            if result["success"]:
                facts["description"] = result["translated_text"]

        if "fun_fact" in facts and facts["fun_fact"]:
            result = translate_text(
                facts["fun_fact"],
                display_lang
            )

            if result["success"]:
                facts["fun_fact"] = result["translated_text"]

        if "best_time" in facts and facts["best_time"]:
            result = translate_text(
                facts["best_time"],
                display_lang
            )

            if result["success"]:
                facts["best_time"] = result["translated_text"]

        facts["language"] = bcp47

        return facts

    except Exception as e:
        print(f"Facts translation error: {str(e)}")
        return facts


def _strip_json_fences(text: str) -> str:
    """
    Removes optional Markdown code fences around Gemini JSON output.

    Handles:
        ```json
        {...}
        ```

    and:
        ```
        {...}
        ```
    """
    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def detect_and_translate(
    image_text: str,
    target_language: str = "English"
) -> dict:
    """
    Detects the source language of OCR text and translates the
    COMPLETE OCR text into the requested target language.

    Designed for:
    - menus
    - signs
    - notices
    - posters
    - multiline OCR content

    The complete multiline translation is preserved.
    """

    try:
        bcp47 = to_bcp47(target_language)
        display_lang = to_display_name(bcp47)

        if not image_text or not image_text.strip():
            return {
                "success": False,
                "error": "No OCR text was provided.",
                "detected_language": "Unknown",
                "translation": "",
                "target_language": display_lang,
            }

        print(
            f"Detecting and translating OCR text "
            f"to {display_lang}..."
        )

        prompt = f"""You are a professional OCR translation system.

The following text was extracted from an image.
It may be a menu, sign, notice, poster, board, or other
multiline document.

Your task:

1. Detect the source language.
2. Translate the ENTIRE OCR text into {display_lang}.
3. Preserve the original structure and line breaks as much
   as possible.
4. Translate EVERY line.
5. Translate headings, menu items, descriptions and instructions.
6. Do NOT summarize.
7. Do NOT omit any line.
8. Preserve prices, numbers, quantities and currency values exactly.
9. Do not invent information.
10. Do not add explanations.
11. Preserve proper nouns where appropriate.
12. The translation field must contain the COMPLETE translation.

Return ONLY valid JSON.

Use EXACTLY this structure:

{{
  "detected_language": "source language name",
  "translation": "complete multiline translation"
}}

Do not use Markdown.
Do not use code fences.
Do not write anything outside the JSON object.

OCR TEXT:
{image_text}
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        raw_reply = (response.text or "").strip()

        print("========== TRANSLATION RESPONSE ==========")
        print(raw_reply)
        print("==========================================")

        if not raw_reply:
            return {
                "success": False,
                "error": "Gemini returned an empty translation response.",
                "detected_language": "Unknown",
                "translation": "",
                "target_language": display_lang,
            }

        detected_language = "Unknown"
        translation = ""

        try:
            cleaned = _strip_json_fences(raw_reply)

            parsed = json.loads(cleaned)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "Gemini response is not a JSON object."
                )

            detected_language = str(
                parsed.get(
                    "detected_language",
                    "Unknown"
                )
            ).strip()

            translation = str(
                parsed.get(
                    "translation",
                    ""
                )
            ).strip()

            if not detected_language:
                detected_language = "Unknown"

            if not translation:
                raise ValueError(
                    "Gemini JSON contained an empty translation."
                )

        except Exception as parse_error:
            """
            Safe fallback.

            Never split the Gemini response line-by-line.
            Treat the COMPLETE response as the translation so
            multiline menu content is not accidentally lost.
            """
            print(
                f"JSON parse fallback triggered: {parse_error}"
            )

            translation = raw_reply
            detected_language = "Unknown"

        return {
            "success": True,
            "detected_language": detected_language,
            "translation": translation,
            "target_language": display_lang,
        }

    except Exception as e:
        print(f"Translation error: {str(e)}")

        try:
            fallback_display_lang = to_display_name(
                to_bcp47(target_language)
            )
        except Exception:
            fallback_display_lang = target_language

        return {
            "success": False,
            "error": str(e),
            "detected_language": "Unknown",
            "translation": "",
            "target_language": fallback_display_lang,
        }