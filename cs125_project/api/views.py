from ..common import *
from ..query_processing import build_request, get_restaurant_recommendations
from ..recommender import rank_places

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
import json

from .models import UserPreference


def _default_prefs_dict() -> dict:
	return {
		"dietary": [],
		"maxPrice": 4,
		"minRating": 0,
		"adventurousness": "Balanced",
		"priceBias": 5.0,
		"cuisines": {},
	}


def _prefs_from_payload(data: dict) -> dict:
	prefs = _default_prefs_dict()
	if not isinstance(data, dict):
		return prefs
	if isinstance(data.get("dietary"), list):
		prefs["dietary"] = [str(x) for x in data.get("dietary", [])]
	if data.get("maxPrice") is not None or data.get("max_price") is not None:
		prefs["maxPrice"] = int(data.get("maxPrice") or data.get("max_price", 4))
	if data.get("minRating") is not None or data.get("min_rating") is not None:
		prefs["minRating"] = float(data.get("minRating") or data.get("min_rating", 0))
	if data.get("adventurousness") is not None:
		prefs["adventurousness"] = str(data["adventurousness"])
	if data.get("priceBias") is not None or data.get("price_bias") is not None:
		prefs["priceBias"] = float(data.get("priceBias") or data.get("price_bias", 5.0))
	if isinstance(data.get("cuisines"), dict):
		prefs["cuisines"] = {str(k): float(v) for k, v in data["cuisines"].items()}
	return prefs


@require_http_methods(["GET"])
def csrf(request: Any):
	"""
	Ensures a CSRF cookie is set and returns token.
	Useful for JS apps using session auth.
	"""
	return JsonResponse({"csrfToken": get_token(request)})


@require_http_methods(["POST"])
def signup(request: Any):
	try:
		data = json.loads(request.body or b"{}")
	except json.JSONDecodeError:
		return JsonResponse({"error": "Invalid JSON"}, status=400)

	email = (data.get("email") or "").strip().lower()
	password = data.get("password") or ""
	if not email or not password:
		return JsonResponse({"error": "Email and password required"}, status=400)

	if User.objects.filter(username=email).exists():
		return JsonResponse({"error": "Account already exists. Please log in."}, status=409)

	user = User.objects.create_user(username=email, email=email, password=password)
	login(request, user)
	UserPreference.objects.get_or_create(user=user)
	return JsonResponse({"ok": True, "email": email})


@require_http_methods(["POST"])
def login_view(request: Any):
	try:
		data = json.loads(request.body or b"{}")
	except json.JSONDecodeError:
		return JsonResponse({"error": "Invalid JSON"}, status=400)

	email = (data.get("email") or "").strip().lower()
	password = data.get("password") or ""
	if not email or not password:
		return JsonResponse({"error": "Email and password required"}, status=400)

	user = authenticate(request, username=email, password=password)
	if user is None:
		return JsonResponse({"error": "Invalid email or password"}, status=401)

	login(request, user)
	UserPreference.objects.get_or_create(user=user)
	return JsonResponse({"ok": True, "email": user.email or email})


@require_http_methods(["POST"])
def logout_view(request: Any):
	logout(request)
	return JsonResponse({"ok": True})


@require_http_methods(["GET", "PUT"])
def preferences(request: Any):
	"""
	GET: return current preferences.
	PUT: save preferences.

	If authenticated, preferences are stored in DB per-user.
	If anonymous, preferences are stored in session.
	"""
	if request.method == "GET":
		if request.user.is_authenticated:
			pref_obj, _ = UserPreference.objects.get_or_create(user=request.user)
			return JsonResponse({"preferences": pref_obj.to_dict(), "authenticated": True})
		return JsonResponse({"preferences": request.session.get("user_prefs", _default_prefs_dict()), "authenticated": False})

	# PUT
	try:
		data = json.loads(request.body or b"{}")
	except json.JSONDecodeError:
		return JsonResponse({"error": "Invalid JSON"}, status=400)

	prefs = _prefs_from_payload(data)

	if request.user.is_authenticated:
		pref_obj, _ = UserPreference.objects.get_or_create(user=request.user)
		pref_obj.dietary = prefs["dietary"]
		pref_obj.max_price = prefs["maxPrice"]
		pref_obj.min_rating = prefs["minRating"]
		pref_obj.adventurousness = prefs["adventurousness"]
		pref_obj.price_bias = prefs["priceBias"]
		pref_obj.cuisines = prefs["cuisines"]
		pref_obj.save()
		return JsonResponse({"ok": True, "preferences": pref_obj.to_dict(), "authenticated": True})

	request.session["user_prefs"] = prefs
	request.session.modified = True
	return JsonResponse({"ok": True, "preferences": prefs, "authenticated": False})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def get_restaurants(request: Any):
	"""
	API endpoint to get restaurant recommendations based on a query.
	
	GET params:
		- query: The search query string (e.g., "cheap vegan restaurants near Irvine")
		- lat: Optional user latitude (float)
		- lng: Optional user longitude (float)
	
	POST body (JSON):
		- query: The search query string
		- lat: Optional user latitude
		- lng: Optional user longitude
		- preferences: Optional preferences dict (dietary restrictions, min_rating, etc.)
	"""
	try:
		# Parse request data
		if request.method == 'POST':
			try:
				data = json.loads(request.body)
				query = data.get('query', '')
				lat = data.get('lat')
				lng = data.get('lng')
				prefs_data = data.get('preferences', {})
			except json.JSONDecodeError:
				return JsonResponse({'error': 'Invalid JSON'}, status=400)
		else:  # GET
			query = request.GET.get('query', '')
			lat = request.GET.get('lat')
			lng = request.GET.get('lng')
			prefs_data = {}
		
		if not query:
			return JsonResponse({'error': 'Query parameter is required'}, status=400)
		
		# Parse user location
		user_location = None
		if lat and lng:
			try:
				user_location = (float(lat), float(lng))
			except (ValueError, TypeError):
				pass  # Invalid coordinates, will use query location extraction
		
		# Build request object for Google Places API
		request_obj = build_request(query, user_location=user_location)
		
		# Get raw recommendations from Google Places API
		raw_recommendations = get_restaurant_recommendations(request_obj, query)
		
		if not raw_recommendations:
			return JsonResponse({'restaurants': [], 'message': 'No restaurants found'})
		
		# Retrieve preferences: from DB if authenticated, else session; merge request overrides
		if request.user.is_authenticated:
			pref_obj, _ = UserPreference.objects.get_or_create(user=request.user)
			base = pref_obj.to_dict()
		else:
			base = request.session.get("user_prefs", _default_prefs_dict()) or _default_prefs_dict()
		# Merge request prefs over base (request overrides); supports camelCase and snake_case
		merged = dict(base)
		override_map = {"max_price": "maxPrice", "min_rating": "minRating", "price_bias": "priceBias"}
		for k, v in (prefs_data or {}).items():
			if v is not None and k in ("dietary", "maxPrice", "minRating", "adventurousness", "priceBias", "cuisines"):
				merged[k] = v
			elif v is not None and k in override_map:
				merged[override_map[k]] = v
		prefs = UserPreferences.from_dict(merged)
		
		# Rank recommendations based on preferences
		ranked_recommendations = rank_places(raw_recommendations, prefs)
		
		# Format response for frontend
		formatted_restaurants = []
		for idx, place in enumerate(ranked_recommendations):
			formatted_place = {
				'id': place.id,
				'name': place.name,
				'lat': place.lat,
				'lng': place.lng,
				'rating': place.rating,
				'price': '$' * (place.price_level if place.price_level else 0),
				'type': ', '.join((place.types if place.types else [])[:2]) if place.types else 'Restaurant',
				'vicinity': place.address,
				'image': '',
			}
			formatted_restaurants.append(formatted_place)
		
		return JsonResponse({'restaurants': formatted_restaurants})
	
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)
