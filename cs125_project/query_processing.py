import re
import os
import requests
from dotenv import load_dotenv
from datetime import datetime


# Handle imports for both module and script execution
try:
    from .api.models import UserPreference
    from .recommender import rank_places
    from .ingestion import AugmentedPlacesRepository, Place
except ImportError:
    # Fallback for when running as script
    from api.models import UserPreference
    from recommender import rank_places
    from ingestion import AugmentedPlacesRepository, Place

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

places_repo = AugmentedPlacesRepository()#force_migrate=True)

def extract_keywords(query):
    # Remove punctuation
    query_clean = re.sub(r'[^\w\s]', '', query)
    keywords = [word.lower() for word in query_clean.split() if word.lower() not in STOPWORDS]
    return " ".join(keywords) if keywords else ""

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
    request_obj["radius"] = radius if radius else 20000
    
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
def get_restaurant_recommendations(request_obj, query: str, prefs: UserPreference, api_key=GOOGLE_API_KEY, top_n=NUM_RECOMMENDATIONS) -> list[Place]:
    params = request_obj.copy()

    if 'lat' in params and 'lng' in params: # location extraction not working for me
        lat = float(params['lat'])
        lng = float(params['lng'])
    else:
        lat = 33.645963
        lng = -117.842825

    print(request_obj)
    print(f'Query2: "{query}"')
    print(prefs)

    builder = places_repo.query_builder()

    builder = builder.within_radius(params['radius'], lat, lng)
    builder = builder.price_between(0, prefs.max_price)
    builder = builder.min_rating(prefs.min_rating)

    keywords = extract_keywords(query).split()

    if 'Vegetarian' in prefs.dietary:
        builder = builder.require_type('vegetarian_restaurant')
    elif 'Vegan' in prefs.dietary:
        builder = builder.require_type('vegan_restaurant')
    elif 'Gluten Free' in prefs.dietary:
        keywords.extend(['gluten', 'gluten-free', 'gluten free'])

    hour = datetime.now().hour

    print('HELLO')
    builder = builder.relevance_by(keywords)
    #builder.exclude_ids(prefs.disliked_places or [])

    places = builder.select(limit=50)

    print([p.relevance for p in places])
    
    return places

if __name__ == "__main__":

    prefs = UserPreference(
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
        raw_recommendations = get_restaurant_recommendations(req, q)
        ranked_recommendations = rank_places(raw_recommendations, prefs)

        print("Top Recommendations:")
        for r in ranked_recommendations:
            print(
                f"- {r.name} ({r.rating if r.rating else 'N/A'} stars) - {r.address} "
                f"| types={r.types}, price={r.price_level}"
            )
        

