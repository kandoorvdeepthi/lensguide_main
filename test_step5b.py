# test_step5b.py — delete after confirming

from agents.vision_agent import classify_ps06_label

with open("path/to/any_test_photo.jpg", "rb") as f:
    image_bytes = f.read()

result = classify_ps06_label(image_bytes)
print(result)
# Expect either:
#   {"matched": True, "label_class": "spice_market_walk"}  (if photo resembles a class)
#   {"matched": False}                                      (if it doesn't — e.g. real landmark photo)