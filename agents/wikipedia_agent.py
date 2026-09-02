import requests

def get_wikipedia_facts(landmark_name: str) -> dict:
    try:
        print(f"Searching Wikipedia for: {landmark_name}")

        # Search Wikipedia
        search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"

        # Clean the landmark name for URL
        cleaned_name = landmark_name.replace(" ", "_")

        response = requests.get(
            search_url + cleaned_name,
            headers={"User-Agent": "LensGuide/1.0"}
        )

        if response.status_code == 200:
            data = response.json()

            # Get description
            description = data.get("extract", "No description available")

            # Limit to 2 sentences
            sentences = description.split(".")
            short_description = ".".join(sentences[:2]) + "."

            # Get image if available
            image_url = None
            if "thumbnail" in data:
                image_url = data["thumbnail"]["source"]

            print(f"Wikipedia found: {data.get('title')}")

            return {
                "found": True,
                "source": "wikipedia",
                "name": data.get("title", landmark_name),
                "description": short_description,
                "full_description": description,
                "image_url": image_url,
                "timings": "Not available",
                "entry_fee": "Not available",
                "best_time": "Not available",
                "fun_fact": "Not available",
                "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }

        else:
            # Try searching with different format
            search_api = "https://en.wikipedia.org/w/api.php"
            search_response = requests.get(search_api, params={
                "action": "query",
                "list": "search",
                "srsearch": landmark_name,
                "format": "json",
                "srlimit": 1
            })

            search_data = search_response.json()
            results = search_data.get("query", {}).get("search", [])

            if results:
                first_result = results[0]["title"]
                retry = requests.get(
                    search_url + first_result.replace(" ", "_"),
                    headers={"User-Agent": "LensGuide/1.0"}
                )
                if retry.status_code == 200:
                    data = retry.json()
                    description = data.get("extract", "")
                    sentences = description.split(".")
                    short_description = ".".join(sentences[:2]) + "."

                    return {
                        "found": True,
                        "source": "wikipedia",
                        "name": data.get("title", landmark_name),
                        "description": short_description,
                        "full_description": description,
                        "image_url": data.get("thumbnail", {}).get("source"),
                        "timings": "Not available",
                        "entry_fee": "Not available",
                        "best_time": "Not available",
                        "fun_fact": "Not available",
                        "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    }

            return {
                "found": False,
                "source": "wikipedia",
                "message": "Not found on Wikipedia",
                "timings": "Not available",
                "entry_fee": "Not available",
                "best_time": "Not available",
                "fun_fact": "Not available"
            }

    except Exception as e:
        print(f"Wikipedia error: {str(e)}")
        return {
            "found": False,
            "source": "wikipedia",
            "message": str(e),
            "timings": "Not available",
            "entry_fee": "Not available",
            "best_time": "Not available",
            "fun_fact": "Not available"
        }