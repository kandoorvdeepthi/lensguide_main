"""
language_map.py — PS-06 migration (Step 4)

Central place for language normalization. PS-06 tables
(poi_facts_kb, place_kb, languages) always use BCP-47 tags
per Rule R6. Flutter and Gemini prompts work in plain English
names. This module is the single translation point between
the two so no other file has to guess.
"""

# Display name -> BCP-47 (what Flutter currently sends)
DISPLAY_TO_BCP47 = {
    "english": "en-IN",
    "hindi": "hi",
    "tamil": "ta",
}

# BCP-47 -> display name (for Gemini prompts, which read better
# with "Hindi" than with "hi" as free text)
BCP47_TO_DISPLAY = {
    "en-IN": "English",
    "hi": "Hindi",
    "ta": "Tamil",
}


def to_bcp47(language: str) -> str:
    """
    Accepts EITHER a display name ('Hindi') OR an already-valid
    BCP-47 tag ('hi') and always returns BCP-47.

    Case-insensitive on display names. Unknown input falls back
    to 'en-IN' rather than raising, so a typo from the client
    never crashes the request.
    """
    if not language:
        return "en-IN"

    key = language.strip().lower()

    if key in DISPLAY_TO_BCP47:
        return DISPLAY_TO_BCP47[key]

    # Already looks like a BCP-47 tag (e.g. 'hi', 'ta', 'en-IN')
    if language in BCP47_TO_DISPLAY:
        return language

    # Unrecognised — safe default, never crash
    print(f"[lang] Unrecognised language '{language}', defaulting to en-IN")
    return "en-IN"


def to_display_name(bcp47: str) -> str:
    """
    Converts a BCP-47 tag to a plain English name for Gemini
    prompts. Falls back to 'English' for anything not mapped.
    """
    return BCP47_TO_DISPLAY.get(bcp47, "English")


def is_english(bcp47_or_display: str) -> bool:
    """Convenience check used wherever we currently skip translation for English."""
    return to_bcp47(bcp47_or_display) == "en-IN"