def score_place(place, prefs):
    score = 0.0

    # Rating
    if place.get("rating"):
        score += place["rating"]

    # Price preference
    if place.get("price_level") is not None:
        score += prefs.price_bias * (2 - place["price_level"])

    # Cuisine affinity
    for t in place.get("types", []):
        score += prefs.cuisines.get(t, 0.0)

    # Dietary filter (hard constraint)
    if prefs.dietary:
        if not prefs.dietary.intersection(set(place.get("types", []))):
            return float("-inf")

    return score


def rank_places(places, prefs):
    return sorted(
        places,
        key=lambda p: score_place(p, prefs),
        reverse=True
    )
