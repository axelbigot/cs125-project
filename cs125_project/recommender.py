try:
    from .ingestion import Place
    from .common import UserPreferences
except ImportError:
    from ingestion import Place
    from common import UserPreferences

from math import radians, cos, sin, sqrt, atan2


def haversine_distance(lat1, lng1, lat2, lng2):
    # https://en.wikipedia.org/wiki/Haversine_formula
    R = 3958.8
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def score_place(place: Place, prefs: UserPreferences, lat, lng):
    score = 0.0

    if place.rating:
        score += place.rating * 2.0
    
    if place.price_level is not None:
        score += prefs.price_bias * (4.0 - place.price_level)

    for t in (place.types or []):
        if t in prefs.cuisines:
            score += prefs.cuisines[t].satisfaction_score
    
    if place.id in prefs.like_places:
        W = 5.0
        if prefs.adventurousness == 'Safe':
            W = 10.0
        elif prefs.adventurousness == 'Experimental':
            # Already visited
            W = -3.0

        score += prefs.like_places[place.id].satisfaction_score * W

    if place.id in prefs.disliked_places:
        score -= 50

    if prefs.adventurousness == 'Safe':
        score += place.rating * 5
    elif prefs.adventurousness == 'Experimental':
        score += len(place.types or []) * 10

    if lat is not None and lng is not None and place.lat is not None and place.lng is not None:
        distance_miles = haversine_distance(lat, lng, place.lat, place.lng)
        score += max(0, 10 - distance_miles)

    if prefs.adventurousness == 'Safe':
        W = 100
    elif prefs.adventurousness == 'Experimental':
        W = 1
    else:
        W = 3
    # score += (100 + place.relevance) * W
    score += place.relevance * -1 * W

    for t in place.types:
        if 'fusion' in t:
            if prefs.adventurousness == 'Safe':
                score -= 100
            elif prefs.adventurousness == 'Experimental':
                score += 100

    return score


def rank_places(places: list[Place], prefs, lat, lng):
    return sorted(
        places,
        key=lambda p: score_place(p, prefs, lat, lng),
        reverse=True
    )
