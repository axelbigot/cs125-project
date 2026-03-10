try:
    from .ingestion import Place
except ImportError:
    from ingestion import Place

def score_place(place: Place, prefs):
    # Hard constraints
    if place.rating and place.rating < prefs.min_rating:
        return float("-inf")
    
    if place.price_level and place.price_level > prefs.max_price:
        return float("-inf")

    if prefs.dietary:
        if not prefs.dietary.intersection(set(place.types if place.types is not None else [])):
            return float("-inf")
            
    score = 0.0

    # Rating
    if place.rating is not None:
        score += place.rating

    if place.price_level is not None:
        # Assume price_level is 0 (cheap) to N (expensive)
        PRICE_WEIGHT = 100.0  # Large to dominate scoring
        score += PRICE_WEIGHT * prefs.price_bias * place.price_level

    # Cuisine affinity
    for t in (place.types if place.types is not None else []):
        score += prefs.cuisine_preferences.get(t, 0.0)


    return score


def rank_places(places: list[Place], prefs):
    return sorted(
        places,
        key=lambda p: score_place(p, prefs),
        reverse=True
    )
