# test_language_step4.py — delete after confirming

from agents.language_map import to_bcp47, to_display_name
from database import search_landmark_with_fallback

# Normalization checks
print(to_bcp47("Hindi"))        # -> hi
print(to_bcp47("hindi"))        # -> hi (case-insensitive)
print(to_bcp47("hi"))           # -> hi (already valid)
print(to_bcp47("Klingon"))      # -> en-IN (safe fallback)
print(to_display_name("ta"))    # -> Tamil

# End-to-end
result_en = search_landmark_with_fallback("Jaipur Bazaar", "English")
print("\nEnglish:", result_en["fun_fact"], "| fact_language:", result_en.get("fact_language"))

result_hi = search_landmark_with_fallback("Jaipur Bazaar", "Hindi")
print("\nHindi:", result_hi["fun_fact"], "| fact_language:", result_hi.get("fact_language"))