from django.conf import settings
from django.db import models


class UserPreference(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences")

	dietary = models.JSONField(default=list, blank=True)
	max_price = models.PositiveSmallIntegerField(default=4)
	min_rating = models.PositiveSmallIntegerField(default=0)
	adventurousness = models.CharField(max_length=32, default="Balanced")

	updated_at = models.DateTimeField(auto_now=True)

	def to_dict(self) -> dict:
		return {
			"dietary": list(self.dietary or []),
			"maxPrice": int(self.max_price),
			"minRating": int(self.min_rating),
			"adventurousness": self.adventurousness,
		}

