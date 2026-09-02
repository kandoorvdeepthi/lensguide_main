import chromadb

client = chromadb.Client()
collection = client.create_collection("landmarks")

landmarks = [
    {
        "id": "gateway_of_india",
        "text": "Gateway of India built in 1924 Mumbai Maharashtra India overlooks Arabian Sea.",
        "name": "Gateway of India",
        "location": "Mumbai, India",
        "timings": "Open 24 hours",
        "entry_fee": "Free",
        "best_time": "Early morning or sunset",
        "fun_fact": "The last British troops left India through this gateway in 1948",
        "latitude": "18.9220",
        "longitude": "72.8347"
    },
    {
        "id": "taj_mahal",
        "text": "Taj Mahal white marble mausoleum built 1632 Emperor Shah Jahan Agra Uttar Pradesh India UNESCO World Heritage Site.",
        "name": "Taj Mahal",
        "location": "Agra, India",
        "timings": "6:00 AM - 7:00 PM (Closed Friday)",
        "entry_fee": "₹50 Indians / ₹1100 Foreigners",
        "best_time": "Sunrise",
        "fun_fact": "It took 22 years and 20,000 workers to build",
        "latitude": "27.1751",
        "longitude": "78.0421"
    },
    {
        "id": "india_gate",
        "text": "India Gate war memorial New Delhi India built 1931 commemorates soldiers World War I.",
        "name": "India Gate",
        "location": "New Delhi, India",
        "timings": "Open 24 hours",
        "entry_fee": "Free",
        "best_time": "Evening when illuminated",
        "fun_fact": "It is 42 metres tall and made of red Bharatpur stone",
        "latitude": "28.6129",
        "longitude": "77.2295"
    },
    {
        "id": "qutub_minar",
        "text": "Qutub Minar minaret built 1193 Qutb ud-Din Aibak Delhi India tallest minaret India 72.5 metres.",
        "name": "Qutub Minar",
        "location": "New Delhi, India",
        "timings": "7:00 AM - 5:00 PM",
        "entry_fee": "₹30 Indians / ₹500 Foreigners",
        "best_time": "Morning",
        "fun_fact": "It is a UNESCO World Heritage Site built over 200 years",
        "latitude": "28.5244",
        "longitude": "77.1855"
    },
    {
        "id": "hawa_mahal",
        "text": "Hawa Mahal Palace of Winds built 1799 Maharaja Sawai Pratap Singh Jaipur Rajasthan India.",
        "name": "Hawa Mahal",
        "location": "Jaipur, India",
        "timings": "9:00 AM - 4:30 PM",
        "entry_fee": "₹50 Indians / ₹200 Foreigners",
        "best_time": "Morning when sunlight hits the facade",
        "fun_fact": "It has 953 windows designed so royal ladies could watch street life without being seen",
        "latitude": "26.9239",
        "longitude": "75.8267"
    },
    {
        "id": "golden_temple",
        "text": "Golden Temple Harmandir Sahib Sikh Gurdwara built 1604 Amritsar Punjab India holiest shrine Sikhism.",
        "name": "Golden Temple",
        "location": "Amritsar, India",
        "timings": "Open 24 hours",
        "entry_fee": "Free",
        "best_time": "Early morning during prayers",
        "fun_fact": "The temple serves free meals to over 100,000 people every day",
        "latitude": "31.6200",
        "longitude": "74.8765"
    },
    {
        "id": "red_fort",
        "text": "Red Fort historic fort built 1648 Mughal Emperor Shah Jahan Delhi India residence Mughal Emperors 200 years.",
        "name": "Red Fort",
        "location": "Delhi, India",
        "timings": "9:30 AM - 4:30 PM (Closed Monday)",
        "entry_fee": "₹35 Indians / ₹500 Foreigners",
        "best_time": "Morning",
        "fun_fact": "India's Prime Minister addresses the nation from here every Independence Day",
        "latitude": "28.6562",
        "longitude": "77.2410"
    },
    {
        "id": "mysore_palace",
        "text": "Mysore Palace historical palace built 1912 Mysore Karnataka India most visited monuments India.",
        "name": "Mysore Palace",
        "location": "Mysore, India",
        "timings": "10:00 AM - 5:30 PM",
        "entry_fee": "₹70 Indians / ₹200 Foreigners",
        "best_time": "Sunday evenings when illuminated",
        "fun_fact": "The palace is illuminated with 97,000 light bulbs every Sunday and on holidays",
        "latitude": "12.3052",
        "longitude": "76.6552"
    },
    {
        "id": "charminar",
        "text": "Charminar monument mosque built 1591 Muhammad Quli Qutb Shah Hyderabad Telangana India.",
        "name": "Charminar",
        "location": "Hyderabad, India",
        "timings": "9:30 AM - 5:30 PM",
        "entry_fee": "₹25 Indians / ₹300 Foreigners",
        "best_time": "Early morning or evening",
        "fun_fact": "It was built to commemorate the end of a deadly plague in the city",
        "latitude": "17.3616",
        "longitude": "78.4747"
    },
    {
        "id": "lotus_temple",
        "text": "Lotus Temple Bahai House Worship built 1986 New Delhi India shaped like lotus flower.",
        "name": "Lotus Temple",
        "location": "New Delhi, India",
        "timings": "9:00 AM - 5:30 PM (Closed Monday)",
        "entry_fee": "Free",
        "best_time": "Morning or late afternoon",
        "fun_fact": "It has won numerous architectural awards and is one of the most visited buildings in the world",
        "latitude": "28.5535",
        "longitude": "77.2588"
    }
]

collection.add(
    documents=[l["text"] for l in landmarks],
    ids=[l["id"] for l in landmarks],
    metadatas=[{
        "name": l["name"],
        "location": l["location"],
        "timings": l["timings"],
        "entry_fee": l["entry_fee"],
        "best_time": l["best_time"],
        "fun_fact": l["fun_fact"]
    } for l in landmarks]
)

print("✅ Database loaded with", len(landmarks), "landmarks!")


def search_landmark(landmark_name: str) -> dict:
    try:
        results = collection.query(
            query_texts=[landmark_name],
            n_results=1
        )

        if results and results["metadatas"] and results["metadatas"][0]:
            facts = results["metadatas"][0][0]
            print("Found in database:", facts["name"])
            return {
                "found": True,
                "name": facts["name"],
                "location": facts["location"],
                "timings": facts["timings"],
                "entry_fee": facts["entry_fee"],
                "best_time": facts["best_time"],
                "fun_fact": facts["fun_fact"]
            }

        return {
            "found": False,
            "message": "Landmark not in database yet"
        }

    except Exception as e:
        print("Database error:", str(e))
        return {
            "found": False,
            "message": str(e)
        }


def search_landmark_with_fallback(landmark_name: str) -> dict:
    # First try ChromaDB
    result = search_landmark(landmark_name)

    if result["found"]:
        result["source"] = "our_database"
        return result

    # If not found → try Wikipedia
    print(f"Not in ChromaDB, trying Wikipedia for: {landmark_name}")
    from agents.wikipedia_agent import get_wikipedia_facts
    wiki_result = get_wikipedia_facts(landmark_name)

    return wiki_result