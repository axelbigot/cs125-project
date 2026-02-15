try:
    from .ingestion import Place
except ImportError:
    from ingestion import Place

def score_place(place: Place, prefs):
    score = 0.0

    # Rating
    if place.rating is not None:
        score += place.rating

    # Price preference
    if place.price_level is not None:
        score += prefs.price_bias * (2 - place.price_level)

    # Cuisine affinity
    for t in (place.types if place.types is not None else []):
        score += prefs.cuisines.get(t, 0.0)

    # Dietary filter (hard constraint)
    if prefs.dietary:
        if not prefs.dietary.intersection(set(place.types if place.types is not None else [])):
            return float("-inf")

    return score


def rank_places(places: list[Place], prefs):
    return sorted(
        places,
        key=lambda p: score_place(p, prefs),
        reverse=True
    )
