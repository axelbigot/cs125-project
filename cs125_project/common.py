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
	PEANUTS = 1
	LACTOSE = 2
	# ...

# Maybe use Google Places types directly?
class RestaurantStyle(Enum):
	SIT_DOWN = 1
	CAFE = 2
	CASUAL = 3
	# ...

# Maybe use Google Places types directly?
class Mealtime(Enum):
	BREAKFAST = 1
	LUNCH = 2
	DINNER = 3
	# ...

# Maybe use Google Places types directly?
class PriceLevel(Enum):
	PRICE_LEVEL_FREE = 1
	PRICE_LEVEL_INEXPENSIVE = 2
	PRICE_LEVEL_MODERATE = 3
	PRICE_LEVEL_EXPENSIVE = 4
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
class Feedback:
	id: str
	satisfaction_score: float

