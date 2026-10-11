# LensGuide

**See. Understand. Explore.**

LensGuide is an AI-powered travel companion built for the Kognivera Hackathon 2026. You point your phone camera at a landmark, sign or menu, and the app identifies it, retrieves grounded facts from a database, translates them, and shows you what's nearby.

Team: [Team Name] | Members: [Member Names]

## What it does

- **Landmark identification** with Google Gemini vision, using two layers:
  - A closed-set PS-06 classifier that ranks up to 3 candidate classes and applies a confidence threshold.
  - An open-world fallback that uses Gemini's recognized name together with the user's GPS coordinates to find the right database entry.
- **Ambiguity handling:** if the classifier isn't confident, the app shows a "Did you mean...?" choice instead of guessing.
- **Grounded facts:** descriptions, timings, entry fees and other details come from the SQLite database for the resolved `poi_id`, not from the LLM.
- **Translation** into English, Hindi and Tamil. Gemini translates only display text; prices, coordinates and IDs are left untouched.
- **Menu/sign OCR translation** that preserves the full multiline text.
- **Nearby places** ranked by distance from the identified POI.
- **AR-style exploration:** nearby POIs appear as markers positioned using GPS distance, bearing and the device compass. These are not true ARCore spatial anchors.

## Architecture

```
Flutter app (camera, GPS, compass, UI)
        |
Flask REST API
        |
AI orchestration (vision, translation, recommendations)
        |
PS-06 SQLite database
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/identify` | Image + language + latitude/longitude, returns identification and facts |
| POST | `/select-candidate` | User picks one class after an ambiguous result |
| POST | `/translate` | Translate a piece of text |
| POST | `/translate-image` | OCR and translate a menu or sign |
| GET | `/xr_scene?poi_id=` | Look up XR scene metadata for a POI |

## Tech stack

- **Frontend:** Flutter (Android), `image_picker`, `geolocator`, `flutter_compass`, `ar_flutter_plugin_plus`, `http`
- **Backend:** Python, Flask
- **AI:** Google Gemini (`gemini-3.6-flash`, with `gemini-2.5-flash` as a retry fallback)
- **Data:** SQLite (PS-06 schema, plus a CIT demo database)

## Demo dataset

PS-06 is a synthetic, generic dataset and does not contain our campus. For a live, walkable demo we created `PS-06_CIT_DEMO.db` with real POIs around Cambridge Institute of Technology, Bengaluru (the campus, a nearby cafe, a temple and a restaurant).

## Running locally

### 1. Backend

```bash
pip install flask flask-cors google-genai python-dotenv pillow requests
```

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_key_here
```

Start the server:

```bash
python main.py
```

It listens on `0.0.0.0:8000`.

### 2. Frontend

Set the backend address in `flutter_app/lib/services/api_service.dart` (`baseUrl`) and in `flutter_app/lib/screen/ar_screen.dart` (`_backendBase`). Use your computer's local network IP so a phone on the same Wi-Fi can reach it, for example `http://192.168.x.x:8000`.

```bash
cd flutter_app
flutter pub get
flutter run
```

For AR testing, use a release build (`flutter build apk --release`). Debug builds are less stable with the AR plugin.

## Known limitations

- Translation supports English, Hindi and Tamil only.
- AR markers are GPS/compass-driven overlays, not world-anchored objects.
- The closed-set classifier recognizes generic place types, so real-world landmarks fall through to the open-world path.
- The demo database covers only the area around CIT.

## Future scope

More cities and landmarks, richer AR anchoring, offline knowledge packs, and personalized itineraries.
