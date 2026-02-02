from typing import *
from dataclasses import dataclass
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
class UserContext:
	prev_restaurants: Dict[str, ScoredRestaurant]
	cuisine_preferences: Dict[CuisineType, ScoredCuisine]
	# Probability that user wants a certain kind of meal at a certan time of day.
	# Dict[<time>, Dict<Lunch|Breakfast|...>, <probablity_wants>]
	datetime_mealtime_distribution: Dict[int, Dict[Mealtime, float]]
	datetime_destination_distribution: Dict[int, Dict[Tuple[float, float], float]]
	datetime_price_level_distribution: Dict[int, Dict[PriceLevel, float]]
	datetime_stars_distribution: Dict[int, Dict[int, float]]
	datetime_adventurous_distribution: Dict[int, Dict[float, float]]
	datetime_group_size_distribution: Dict[int, Dict[int, float]]
	datetime_proximity_miles_distribution: Dict[int, Dict[float, float]]
	datetime_restaurant_style_distribution: Dict[int, Dict[RestaurantStyle, float]]
	datetime_dietary_restrictions_distribution: Dict[int, Dict[DietaryRestriction, float]]

	hard_min_price_level: PriceLevel
	hard_max_price_level: PriceLevel

@dataclass
class Feedback:
	id: str
	satisfaction_score: float

@dataclass
class UserPreferences:
	pass
