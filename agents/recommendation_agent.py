import os
import requests
from dotenv import load_dotenv

load_dotenv()

# =====================
# HARDCODED NEARBY DATA
# For demo purposes
# =====================
NEARBY_DATA = {
    "gateway of india": {
        "hotels": [
            {"name": "Taj Mahal Palace Hotel", "distance": "0.2 km", "rating": 4.8, "type": "hotel"},
            {"name": "The Oberoi Mumbai", "distance": "1.2 km", "rating": 4.7, "type": "hotel"},
            {"name": "Gordon House Hotel", "distance": "0.8 km", "rating": 4.2, "type": "hotel"}
        ],
        "restaurants": [
            {"name": "Leopold Cafe", "distance": "0.5 km", "rating": 4.3, "type": "restaurant"},
            {"name": "Bade Miya", "distance": "0.7 km", "rating": 4.5, "type": "restaurant"},
            {"name": "Khyber Restaurant", "distance": "1.0 km", "rating": 4.4, "type": "restaurant"}
        ],
        "attractions": [
            {"name": "Elephanta Caves", "distance": "10 km", "rating": 4.5, "type": "attraction"},
            {"name": "Colaba Causeway", "distance": "0.5 km", "rating": 4.2, "type": "attraction"},
            {"name": "Marine Drive", "distance": "2.0 km", "rating": 4.6, "type": "attraction"}
        ]
    },
    "taj mahal": {
        "hotels": [
            {"name": "The Oberoi Amarvilas", "distance": "0.6 km", "rating": 4.9, "type": "hotel"},
            {"name": "Trident Agra", "distance": "1.5 km", "rating": 4.5, "type": "hotel"},
            {"name": "ITC Mughal", "distance": "2.0 km", "rating": 4.6, "type": "hotel"}
        ],
        "restaurants": [
            {"name": "Peshawri", "distance": "1.0 km", "rating": 4.4, "type": "restaurant"},
            {"name": "Dasaprakash", "distance": "1.5 km", "rating": 4.2, "type": "restaurant"},
            {"name": "Pinch of Spice", "distance": "2.0 km", "rating": 4.3, "type": "restaurant"}
        ],
        "attractions": [
            {"name": "Agra Fort", "distance": "2.5 km", "rating": 4.5, "type": "attraction"},
            {"name": "Mehtab Bagh", "distance": "1.5 km", "rating": 4.3, "type": "attraction"},
            {"name": "Fatehpur Sikri", "distance": "40 km", "rating": 4.4, "type": "attraction"}
        ]
    },
    "india gate": {
        "hotels": [
            {"name": "The Leela Palace", "distance": "1.0 km", "rating": 4.8, "type": "hotel"},
            {"name": "Taj Mahal Hotel Delhi", "distance": "1.5 km", "rating": 4.7, "type": "hotel"},
            {"name": "The Imperial Hotel", "distance": "2.0 km", "rating": 4.6, "type": "hotel"}
        ],
        "restaurants": [
            {"name": "Bukhara", "distance": "2.0 km", "rating": 4.6, "type": "restaurant"},
            {"name": "Dum Pukht", "distance": "1.5 km", "rating": 4.5, "type": "restaurant"},
            {"name": "Sanjha Chulha", "distance": "1.0 km", "rating": 4.3, "type": "restaurant"}
        ],
        "attractions": [
            {"name": "Rashtrapati Bhavan", "distance": "2.0 km", "rating": 4.5, "type": "attraction"},
            {"name": "National Museum", "distance": "1.5 km", "rating": 4.4, "type": "attraction"},
            {"name": "Lodhi Garden", "distance": "3.0 km", "rating": 4.6, "type": "attraction"}
        ]
    },
    "qutub minar": {
        "hotels": [
            {"name": "Bloomrooms at Link Road", "distance": "1.0 km", "rating": 4.2, "type": "hotel"},
            {"name": "Radisson Blu Dwarka", "distance": "3.0 km", "rating": 4.4, "type": "hotel"},
            {"name": "The Grand New Delhi", "distance": "4.0 km", "rating": 4.5, "type": "hotel"}
        ],
        "restaurants": [
            {"name": "Olive Bar and Kitchen", "distance": "0.5 km", "rating": 4.4, "type": "restaurant"},
            {"name": "Indian Accent", "distance": "3.0 km", "rating": 4.7, "type": "restaurant"},
            {"name": "Lodi Garden Restaurant", "distance": "4.0 km", "rating": 4.3, "type": "restaurant"}
        ],
        "attractions": [
            {"name": "Mehrauli Archaeological Park", "distance": "0.3 km", "rating": 4.3, "type": "attraction"},
            {"name": "Jamali Kamali Mosque", "distance": "0.5 km", "rating": 4.2, "type": "attraction"},
            {"name": "Garden of Five Senses", "distance": "2.0 km", "rating": 4.1, "type": "attraction"}
        ]
    },
    "hawa mahal": {
        "hotels": [
            {"name": "Rambagh Palace", "distance": "3.0 km", "rating": 4.8, "type": "hotel"},
            {"name": "Samode Haveli", "distance": "1.0 km", "rating": 4.6, "type": "hotel"},
            {"name": "Hotel Pearl Palace", "distance": "0.5 km", "rating": 4.3, "type": "hotel"}
        ],
        "restaurants": [
            {"name": "Peacock Rooftop Restaurant", "distance": "0.3 km", "rating": 4.4, "type": "restaurant"},
            {"name": "Rawat Misthan Bhandar", "distance": "1.0 km", "rating": 4.5, "type": "restaurant"},
            {"name": "LMB Restaurant", "distance": "0.8 km", "rating": 4.3, "type": "restaurant"}
        ],
        "attractions": [
            {"name": "City Palace Jaipur", "distance": "0.8 km", "rating": 4.5, "type": "attraction"},
            {"name": "Jantar Mantar", "distance": "1.0 km", "rating": 4.3, "type": "attraction"},
            {"name": "Amber Fort", "distance": "11 km", "rating": 4.6, "type": "attraction"}
        ]
    },
    "golden temple": {
        "hotels": [
            {"name": "Hyatt Amritsar", "distance": "2.0 km", "rating": 4.5, "type": "hotel"},
            {"name": "Hotel Mohan International", "distance": "0.5 km", "rating": 4.2, "type": "hotel"},
            {"name": "Ramada Amritsar", "distance": "3.0 km", "rating": 4.3, "type": "hotel"}
        ],
        "restaurants": [
            {"name": "Langar at Golden Temple", "distance": "0.0 km", "rating": 5.0, "type": "restaurant"},
            {"name": "Bharawan Da Dhaba", "distance": "0.8 km", "rating": 4.5, "type": "restaurant"},
            {"name": "Kesar Da Dhaba", "distance": "1.0 km", "rating": 4.4, "type": "restaurant"}
        ],
        "attractions": [
            {"name": "Jallianwala Bagh", "distance": "0.5 km", "rating": 4.5, "type": "attraction"},
            {"name": "Wagah Border", "distance": "28 km", "rating": 4.6, "type": "attraction"},
            {"name": "Durgiana Temple", "distance": "2.0 km", "rating": 4.3, "type": "attraction"}
        ]
    },
    "red fort": {
        "hotels": [
            {"name": "Hotel Broadway", "distance": "1.0 km", "rating": 4.2, "type": "hotel"},
            {"name": "Maidens Hotel", "distance": "1.5 km", "rating": 4.3, "type": "hotel"},
            {"name": "The Lalit New Delhi", "distance": "3.0 km", "rating": 4.5, "type": "hotel"}
        ],
        "restaurants": [
            {"name": "Karim's", "distance": "0.5 km", "rating": 4.5, "type": "restaurant"},
            {"name": "Al Jawahar", "distance": "0.6 km", "rating": 4.3, "type": "restaurant"},
            {"name": "Paranthe Wali Gali", "distance": "1.0 km", "rating": 4.4, "type": "restaurant"}
        ],
        "attractions": [
            {"name": "Jama Masjid", "distance": "0.8 km", "rating": 4.5, "type": "attraction"},
            {"name": "Chandni Chowk", "distance": "0.5 km", "rating": 4.3, "type": "attraction"},
            {"name": "Raj Ghat", "distance": "2.0 km", "rating": 4.4, "type": "attraction"}
        ]
    }
}


def get_nearby_places_hardcoded(landmark_name: str) -> dict:
    """Get hardcoded nearby places for known landmarks"""
    key = landmark_name.lower().strip()

    # Try exact match first
    if key in NEARBY_DATA:
        return {
            "found": True,
            "source": "hardcoded",
            "landmark": landmark_name,
            "nearby": NEARBY_DATA[key]
        }

    # Try partial match
    for landmark_key in NEARBY_DATA:
        if landmark_key in key or key in landmark_key:
            return {
                "found": True,
                "source": "hardcoded",
                "landmark": landmark_name,
                "nearby": NEARBY_DATA[landmark_key]
            }

    return {
        "found": False,
        "source": "hardcoded",
        "nearby": {
            "hotels": [],
            "restaurants": [],
            "attractions": []
        }
    }


def get_nearby_places_google(latitude: float, longitude: float) -> dict:
    """Get real nearby places from Google Places API"""
    try:
        api_key = os.getenv("GOOGLE_PLACES_KEY")

        if not api_key or api_key == "leave-empty-for-now":
            print("Google Places API key not set — using hardcoded data")
            return {"found": False}

        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        nearby = {"hotels": [], "restaurants": [], "attractions": []}

        for place_type in ["lodging", "restaurant", "tourist_attraction"]:
            response = requests.get(url, params={
                "location": f"{latitude},{longitude}",
                "radius": 2000,
                "type": place_type,
                "key": api_key
            })

            results = response.json().get("results", [])[:3]

            for place in results:
                category = "hotels" if place_type == "lodging" else \
                          "restaurants" if place_type == "restaurant" else \
                          "attractions"

                nearby[category].append({
                    "name": place["name"],
                    "rating": place.get("rating", "N/A"),
                    "address": place.get("vicinity", ""),
                    "type": category
                })

        return {
            "found": True,
            "source": "google_places",
            "nearby": nearby
        }

    except Exception as e:
        print(f"Google Places error: {str(e)}")
        return {"found": False}


def get_nearby_places(landmark_name: str, latitude: float = None, longitude: float = None) -> dict:
    """
    Main function — tries Google Places first, falls back to hardcoded
    """
    # Try Google Places if coordinates provided
    if latitude and longitude:
        google_result = get_nearby_places_google(latitude, longitude)
        if google_result["found"]:
            return google_result

    # Fall back to hardcoded data
    return get_nearby_places_hardcoded(landmark_name)