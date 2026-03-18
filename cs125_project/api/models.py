from django.conf import settings
from django.db import models


class UserPreference(models.Model):
	"""Django model storing the same fields as common.UserPreferences for ranking."""
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences")

	dietary = models.JSONField(default=list, blank=True)
	max_price = models.PositiveSmallIntegerField(default=4)
	min_rating = models.FloatField(default=0.0)
	adventurousness = models.CharField(max_length=32, default="Balanced")
	price_bias = models.FloatField(default=5.0)
	cuisines = models.JSONField(default=dict, blank=True)  # {place_type: score}
	liked_places = models.JSONField(default=list, blank=True)
	disliked_places = models.JSONField(default=list, blank=True)

	top_searches = models.JSONField(default=dict, blank=True)

	updated_at = models.DateTimeField(auto_now=True)

	def to_dict(self) -> dict:
		"""API response shape (camelCase). Matches what UserPreferences.from_dict expects."""
		return {
			"dietary": list(self.dietary or []),
			"maxPrice": int(self.max_price),
			"minRating": float(self.min_rating),
			"adventurousness": self.adventurousness,
			"priceBias": float(self.price_bias),
			"cuisines": dict(self.cuisines or {}),
		}

	def to_user_preferences(self):
		"""Return a common.UserPreferences instance for use in ranking."""
		from ..api.models import UserPreference
		return UserPreference.from_dict(self.to_dict())

