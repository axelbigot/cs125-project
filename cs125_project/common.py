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
class UserPreferences:
	cuisine_preferences: Dict[CuisineType, ScoredCuisine] = field(default_factory=dict)
	price_bias: float = 5
	max_price: int = 4
	min_rating: float = 0.0
	adventurousness: str = "Balanced"
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
	
	def _normalize_distribution(self, dist: Dict[Any, float]) -> Dict[Any, float]:
		total = float(sum(dist.values())) if dist else 0.0
		if total <= 0.0:
			return {}
		return {k: v / total for k, v in dist.items()}

	def record_mealtime(self, hour: int, mealtime: Mealtime, weight: float = 1.0) -> None:
		"""
		Update datetime_mealtime_distribution for a given hour of day and mealtime.
		hour: 0–23 (local hour bucket)
		"""
		if weight <= 0:
			return
		bucket = self.datetime_mealtime_distribution.setdefault(int(hour), {})
		bucket[mealtime] = bucket.get(mealtime, 0.0) + float(weight)

	def get_mealtime_distribution(self, hour: int) -> Dict[Mealtime, float]:
		"""
		Return normalized probability distribution of mealtimes for a given hour.
		"""
		raw = self.datetime_mealtime_distribution.get(int(hour), {})
		return self._normalize_distribution(raw)

	def record_adventurousness(self, hour: int, adventurous_value: float, weight: float = 1.0) -> None:
		"""
		Update datetime_adventurous_distribution for a given hour with an observed adventurousness score.
		adventurous_value is typically in [1, 5].
		"""
		if weight <= 0:
			return
		bucket = self.datetime_adventurous_distribution.setdefault(int(hour), {})
		bucket[float(adventurous_value)] = bucket.get(float(adventurous_value), 0.0) + float(weight)

	def get_expected_adventurousness(self, hour: int) -> Optional[float]:
		"""
		Compute the expected adventurousness value for the given hour, or None if unknown.
		"""
		raw = self.datetime_adventurous_distribution.get(int(hour), {})
		if not raw:
			return None
		norm = self._normalize_distribution(raw)
		return sum(value * prob for value, prob in norm.items())

	def record_proximity(self, hour: int, proximity_miles: float, weight: float = 1.0) -> None:
		"""
		Update datetime_proximity_miles_distribution with an observed preferred search radius.
		"""
		if weight <= 0:
			return
		bucket = self.datetime_proximity_miles_distribution.setdefault(int(hour), {})
		bucket[float(proximity_miles)] = bucket.get(float(proximity_miles), 0.0) + float(weight)

	def get_expected_proximity(self, hour: int) -> Optional[float]:
		"""
		Compute the expected preferred search radius (in miles) for the given hour, or None.
		"""
		raw = self.datetime_proximity_miles_distribution.get(int(hour), {})
		if not raw:
			return None
		norm = self._normalize_distribution(raw)
		return sum(radius * prob for radius, prob in norm.items())

	def record_restaurant_style(self, hour: int, style: RestaurantStyle, weight: float = 1.0) -> None:
		"""
		Update datetime_restaurant_style_distribution with an observed preferred style.
		"""
		if weight <= 0:
			return
		bucket = self.datetime_restaurant_style_distribution.setdefault(int(hour), {})
		bucket[style] = bucket.get(style, 0.0) + float(weight)

	def get_restaurant_style_distribution(self, hour: int) -> Dict[RestaurantStyle, float]:
		"""
		Return normalized probability distribution of restaurant styles for the given hour.
		"""
		raw = self.datetime_restaurant_style_distribution.get(int(hour), {})
		return self._normalize_distribution(raw)

	def update_from_click(self, place: Dict[str, Any]) -> None:
		"""
		Update coarse-grained preferences from a clicked place document.
		Currently adjusts price_bias; can be extended to use cuisine types.
		"""
		if place.get("price_level") is not None:
			self.price_bias += (2 - place["price_level"]) * 0.1

	def dislikes(self, place_id: str) -> None:
		self.disliked_places[place_id] = ScoredRestaurant(satisfaction_score=0.0)

@dataclass
class Feedback:
	id: str
	satisfaction_score: float

