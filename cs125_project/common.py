import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

from typing import *
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


# Maybe use Google Places types directly?
class DietaryRestriction(Enum):
	PEANUTS = 1,
	LACTOSE = 2,
	# ...

# Maybe use Google Places types directly?
class RestaurantStyle(Enum):
	SIT_DOWN = 1,
	CAFE = 2,
	CASUAL = 3
	# ...

# Maybe use Google Places types directly?
class Mealtime(Enum):
	BREAKFAST = 1,
	LUNCH = 2,
	DINNER = 3,
	# ...

# Maybe use Google Places types directly?
class PriceLevel(Enum):
	PRICE_LEVEL_FREE = 1,
	PRICE_LEVEL_INEXPENSIVE = 2,
	PRICE_LEVEL_MODERATE = 3,
	PRICE_LEVEL_EXPENSIVE = 4,
	PRICE_LEVEL_VERY_EXPENSIVE = 5

# Maybe use Google Places types directly?
class CuisineType(Enum):
	pass

@dataclass
class QueryRequest:
	lng: float
	lat: float
	datetime: float
	query_string: str
	dietary_restrictions: List[DietaryRestriction]
	proximity_miles: float
	restaurant_style: RestaurantStyle
	adventurous_sentiment: float # [1, 5]
	group_size: int
	min_stars: int # [1, 5]
	max_stars: int # [1, 5]
	min_price_level: PriceLevel
	max_price_level: PriceLevel
	opt_mealtime: Optional[Mealtime]

@dataclass
class ProcessedQuery:
	cuisine_types: List[CuisineType]
	food_modifier: Optional[str]
	# ...

@dataclass
class ApiRequest(QueryRequest, ProcessedQuery):
	pass

@dataclass
class ScoredRestaurant:
	satisfaction_score: float

@dataclass
class ScoredCuisine:
	satisfaction_score: float

@dataclass
class UserPreferences:
	cuisine_preferences: Dict[CuisineType, ScoredCuisine] = field(default_factory=dict)
	price_bias: float = 5
	min_rating: float = 0.0
	disliked_places: Dict[str, ScoredRestaurant] = field(default_factory=dict)
	like_places: Dict[str, ScoredRestaurant] = field(default_factory=dict)
	dietary: set = field(default_factory=set) # vegan, halal, etc
	hard_min_price_level: PriceLevel = PriceLevel.PRICE_LEVEL_FREE
	hard_max_price_level: PriceLevel = PriceLevel.PRICE_LEVEL_VERY_EXPENSIVE
	
	# Probability that user wants a certain kind of meal at a certan time of day.
	# Dict[<time>, Dict<Lunch|Breakfast|...>, <probablity_wants>]
	datetime_mealtime_distribution: Dict[int, Dict[Mealtime, float]] = field(default_factory=dict)
	datetime_adventurous_distribution: Dict[int, Dict[float, float]] = field(default_factory=dict)
	datetime_proximity_miles_distribution: Dict[int, Dict[float, float]] = field(default_factory=dict)
	datetime_restaurant_style_distribution: Dict[int, Dict[RestaurantStyle, float]] = field(default_factory=dict)


	def update_from_click(self, place):
		if "types" in place:
			for t in place["types"]:
				self.cuisines[t] += 1.0
		
		if place.get("price_level") is not None:
			self.price_bias += (2 - place["price_level"]) * 0.1
	
	def dislikes(self, place_id):
		self.disliked_places.add(place_id)

@dataclass
class Feedback:
	id: str
	satisfaction_score: float

