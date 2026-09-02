from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def translate_text(text: str, target_language: str = "English") -> dict:
    try:
        print(f"Translating to {target_language}...")

        prompt = f"""Translate the following text to {target_language}.
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
            "target_language": target_language
        }

    except Exception as e:
        print(f"Translation error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def translate_facts(facts: dict, target_language: str = "English") -> dict:
    try:
        # Don't translate if English
        if target_language.lower() == "english":
            return facts

        print(f"Translating facts to {target_language}...")

        # Translate description
        if "description" in facts and facts["description"]:
            result = translate_text(facts["description"], target_language)
            if result["success"]:
                facts["description"] = result["translated_text"]

        # Translate fun fact
        if "fun_fact" in facts and facts["fun_fact"]:
            result = translate_text(facts["fun_fact"], target_language)
            if result["success"]:
                facts["fun_fact"] = result["translated_text"]

        # Translate best time
        if "best_time" in facts and facts["best_time"]:
            result = translate_text(facts["best_time"], target_language)
            if result["success"]:
                facts["best_time"] = result["translated_text"]

        # Translate timings
        if "timings" in facts and facts["timings"]:
            result = translate_text(facts["timings"], target_language)
            if result["success"]:
                facts["timings"] = result["translated_text"]

        # Translate entry fee
        if "entry_fee" in facts and facts["entry_fee"]:
            result = translate_text(facts["entry_fee"], target_language)
            if result["success"]:
                facts["entry_fee"] = result["translated_text"]

        facts["language"] = target_language
        return facts

    except Exception as e:
        print(f"Facts translation error: {str(e)}")
        return facts


def detect_and_translate(image_text: str, target_language: str = "English") -> dict:
    try:
        print(f"Detecting language and translating...")

        prompt = f"""Look at this text and:
        1. Detect what language it is
        2. Translate it to {target_language}
        
        Text: {image_text}
        
        Reply EXACTLY like this:
        DETECTED_LANGUAGE: [language name]
        TRANSLATION: [translated text]"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        result = response.text.strip()
        lines = result.split("\n")
        parsed = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                parsed[key.strip()] = value.strip()

        return {
            "success": True,
            "detected_language": parsed.get("DETECTED_LANGUAGE", "Unknown"),
            "translation": parsed.get("TRANSLATION", ""),
            "target_language": target_language
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }