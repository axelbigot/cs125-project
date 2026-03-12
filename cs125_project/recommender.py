try:
    from .ingestion import Place
    from .common import UserPreferences
except ImportError:
    from ingestion import Place
    from common import UserPreferences

def score_place(place: Place, prefs: UserPreferences):
    score = 0.0

    if place.rating:
        score += place.rating * 2.0
    
    if place.price_level is not None:
        score += prefs.price_bias * (4.0 - place.price_level)

    for t in (place.types or []):
        if t in prefs.cuisine_preferences:
            score += prefs.cuisine_preferences[t].satisfaction_score
    
    if place.id in prefs.like_places:
        W = 5.0
        if prefs.adventurousness == 'Safe':
            W = 10.0
        elif prefs.adventurousness == 'Experimental':
            # Already visited
            W = -3.0

        score += prefs.like_places[place.id].satisfaction_score * 10

    if place.id in prefs.disliked_places:
        score -= 50

    if prefs.adventurousness == 'Safe':
        score += place.rating * 0.5
    elif prefs.adventurousness == 'Experimental':
        score += len(place.types or []) * 0.3

    return score


def rank_places(places: list[Place], prefs):
    return sorted(
        places,
        key=lambda p: score_place(p, prefs),
        reverse=True
    )
