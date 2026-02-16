from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class UserPreferences:
    cuisines: dict = field(default_factory = lambda: defaultdict(float))
    price_bias: float = 5     # negative = cheaper preference
    min_rating: float = 0.0
    disliked_places: set = field(default_factory = set)
    dietary: set = field(default_factory = set)     # vegan, halal, etc

    def update_from_click(self, place):
        if "types" in place:
            for t in place["types"]:
                self.cuisines[t] += 1.0
        
        if place.get("price_level") is not None:
            self.price_bias += (2-place["price_level"]) * 0.1
        
    def dislikes(self, place_id):
        self.disliked_places.add(place_id)