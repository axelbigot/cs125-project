import re
import os
import requests
from dotenv import load_dotenv

# Handle imports for both module and script execution
try:
    from .preferences import UserPreferences
    from .recommender import rank_places
except ImportError:
    # Fallback for when running as script
    from preferences import UserPreferences
    from recommender import rank_places

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

NUM_RECOMMENDATIONS = 10
STOPWORDS = set((
    "a an the and or but if then else for of to in on at by with without from as "
    "is are was were be been being this that these those it its im youre we you "
    "they he she them our your their some my"
).split())


# Type mapping for Google Places API
TYPE_MAPPING = {
    "restaurant": "restaurant",
    "cafe": "cafe",
    "coffee shop": "cafe",
    "bar": "bar"
}

PRICE_MAPPING = {
    "cheap": (0, 1),
    "moderate": (2, 2),
    "mid-range": (2, 2),
    "expensive": (3, 4)
}

# Regex for distance
DISTANCE_REGEX = r'(\d+)\s*(mile|km|m|meter|meters)'

# Open now keywords
OPEN_NOW_KEYWORDS = ["open now", "currently open"]

def extract_keywords(query):
    # Remove punctuation
    query_clean = re.sub(r'[^\w\s]', '', query)
    keywords = [word.lower() for word in query_clean.split() if word.lower() not in STOPWORDS]
    return " ".join(keywords) if keywords else None

def extract_type(query):
    query_lower = query.lower()
    for keyword, google_type in TYPE_MAPPING.items():  
        if keyword in query_lower:
            return google_type
    return "restaurant"  # default

def extract_price(query):
    for word, (minp, maxp) in PRICE_MAPPING.items():
        if word in query.lower():
            return minp, maxp
    return None, None

def extract_open_now(query):
    query_lower = query.lower()
    return any(kw in query_lower for kw in OPEN_NOW_KEYWORDS)

def extract_radius(query):
    match = re.search(DISTANCE_REGEX, query.lower())
    if match:
        value, unit = match.groups()
        value = float(value)
        if "mile" in unit:
            return int(value * 1609.34)  # miles to meters
        elif "km" in unit:
            return int(value * 1000)     # km to meters
        elif "m" in unit:
            return int(value)            # meters
    return None

# Extract location from a query and geocode it using Google Geocoding API.
# Returns (lat, lng) or user_location fallback.
def extract_location(query, user_location=None):
    """
    Extract location from query and return as "lat,lng" string.
    Uses Google Geocoding API. Falls back to user_location if needed.
    """
    # Look for "near XYZ" or "in XYZ"
    loc_match = re.search(r'(?:near|in)\s+([a-zA-Z\s]+)', query.lower())
    if loc_match:
        location_name = loc_match.group(1).strip()
        
        # Call Google Geocoding API
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": location_name,
            "key": GOOGLE_API_KEY
        }
        response = requests.get(geocode_url, params=params)
        data = response.json()
        
        if data["status"] == "OK" and data["results"]:
            lat = data["results"][0]["geometry"]["location"]["lat"]
            lng = data["results"][0]["geometry"]["location"]["lng"]
            return f"{lat},{lng}"
        else:
            print(f"Geocoding failed for '{location_name}': {data.get('status')}")
    
    # Fallback to user location if provided
    if user_location:
        return f"{user_location[0]},{user_location[1]}"

    # Fallback to user location if provided
    return user_location

def build_request(query, user_location=None):
    keywords = extract_keywords(query)
    minprice, maxprice = extract_price(query)
    opennow = extract_open_now(query)
    radius = extract_radius(query)
    location = extract_location(query, user_location=user_location)
    place_type = extract_type(query)
    
    request_obj = {}
    
    if location:
        request_obj["location"] = location
        
    # Nearby Search requires radius OR rankby=distance
    # if radius is provided, return based on popularity/relevance
    if radius:
        request_obj["radius"] = radius
        # request_obj["rankby"] = "prominence"
    else:
        request_obj["rankby"] = "distance"
    
    if keywords:
        request_obj["keyword"] = keywords
    if place_type is not None:
        request_obj["type"] = place_type
    if minprice is not None:
        request_obj["minprice"] = minprice
    if maxprice is not None:
        request_obj["maxprice"] = maxprice
    if opennow:
        request_obj["opennow"] = True
    
    return request_obj

#Sends a Nearby Search request to Google Places API and returns top N restaurant recommendations.
def get_restaurant_recommendations(request_obj, api_key=GOOGLE_API_KEY, top_n=NUM_RECOMMENDATIONS):
    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    # Google API expects location as "lat,lng" string
    params = request_obj.copy()
    if "location" in params:
        if isinstance(params["location"], tuple):
            params["location"] = f"{params['location'][0]},{params['location'][1]}"

    # Add API key
    params["key"] = api_key

    response = requests.get(base_url, params=params)
    data = response.json()

    if data.get("status") != "OK":
        print(f"API call failed: {data.get('status')}")
        return []
    
    results = []
    for place in data.get("results", [])[:top_n]:
        results.append(place)
    
    return results

if __name__ == "__main__":

    prefs = UserPreferences(
        dietary = {"vegan_restaurant"},
        min_rating = 4.5
    )

    queries = [
        "we want cheap sandwiches near Irvine",
        "some vegan restaurants open now in Newport Beach!",
        "coffee shops within 5 miles of my location"
    ]

    # Irvine (Fallback location if not provided in query)
    user_location = (33.6846, -117.8265)  

    for q in queries:
        req = build_request(q, user_location=user_location)
        print(f"\nQuery: {q}")
        print("Request Object:", req)
        
        # Call API
        raw_recommendations = get_restaurant_recommendations(req)
        ranked_recommendations = rank_places(raw_recommendations, prefs)

        print("Top Recommendations:")
        for r in ranked_recommendations:
            print(
                f"- {r['name']} ({r.get('rating', 'N/A')} stars) - {r.get('vicinity')} "
                f"| types={r.get('types', [])}, price={r.get('price_level')}"
            )
        

