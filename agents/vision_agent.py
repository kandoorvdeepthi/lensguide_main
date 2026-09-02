from google import genai
import os
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def identify_landmark(image_bytes: bytes) -> dict:
    try:
        print("🔍 Vision agent called!")
        print("API Key starts with:", str(os.getenv("GOOGLE_API_KEY"))[:10])

        image = Image.open(io.BytesIO(image_bytes))
        print("✅ Image opened successfully!")

        prompt = """You are a travel assistant.
        Look at this image carefully.
        
        If you see a landmark reply EXACTLY:
        TYPE: landmark
        NAME: [landmark name]
        LOCATION: [city, country]
        
        If you see a sign or menu reply EXACTLY:
        TYPE: text
        CONTENT: [text you see]
        LANGUAGE: [language]
        
        If unknown reply EXACTLY:
        TYPE: unknown
        MESSAGE: Cannot identify"""

        print("🤖 Sending to Gemini...")
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[prompt, image]
        )

        result = response.text
        print("✅ Gemini says:", result)

        lines = result.strip().split("\n")
        parsed = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                parsed[key.strip()] = value.strip()

        print("✅ Parsed result:", parsed)
        return parsed

    except Exception as e:
        print("❌ ERROR in vision agent:", str(e))
        return {"TYPE": "error", "MESSAGE": str(e)}