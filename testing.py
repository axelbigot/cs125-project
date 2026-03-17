import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cs125_project.settings")

import django
django.setup()

from django.contrib.auth.models import User 
from cs125_project.common import Mealtime, RestaurantStyle
from cs125_project.api.models import UserPreference 


def main() -> None:
	# Try to load an existing user preference (if the user exists)
	username = "ngoe5@uci.edu"
	try:
		u = User.objects.get(username=username)
		print(f"Existing preferences for {username}:", getattr(u, "preferences", None).to_dict())
	except User.DoesNotExist:
		print(f"No user with username={username!r} found; skipping DB preference check.")
	except AttributeError:
		print(f"User {username!r} has no attached preferences yet.")
	print('--------------------------------------------------------------')

	# Get user's preferences and exercise the record/get methods
	pref_obj, _ = UserPreference.objects.get_or_create(user=u)
	prefs = pref_obj.to_user_preferences()

	# Record a few events
	prefs.record_mealtime(hour=12, mealtime=Mealtime.LUNCH)
	prefs.record_mealtime(hour=12, mealtime=Mealtime.LUNCH)
	prefs.record_mealtime(hour=12, mealtime=Mealtime.DINNER)

	prefs.record_adventurousness(hour=18, adventurous_value=5)
	prefs.record_adventurousness(hour=18, adventurous_value=3)
	prefs.record_adventurousness(hour=18, adventurous_value=3)

	prefs.record_proximity(hour=9, proximity_miles=2)
	prefs.record_proximity(hour=9, proximity_miles=5)

	prefs.record_restaurant_style(hour=20, style=RestaurantStyle.SIT_DOWN)
	prefs.record_restaurant_style(hour=20, style=RestaurantStyle.CASUAL)
	prefs.record_restaurant_style(hour=20, style=RestaurantStyle.CASUAL)

	print("Mealtime dist @12:", prefs.get_mealtime_distribution(12))
	print("Expected adventurousness @18:", prefs.get_expected_adventurousness(18))
	print("Expected proximity @9:", prefs.get_expected_proximity(9))
	print("Style dist @20:", prefs.get_restaurant_style_distribution(20))

	print('--------------------------------------------------------------')

	print(prefs)


if __name__ == "__main__":
	main()