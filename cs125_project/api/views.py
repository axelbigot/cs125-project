from ..common import *
from ..query_processing import build_request, get_restaurant_recommendations
from ..recommender import rank_places
from ..preferences import UserPreferences

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


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
		
		# Create user preferences from request data
		prefs = UserPreferences(
			dietary=set(prefs_data.get('dietary', [])),
			min_rating=prefs_data.get('min_rating', 0.0)
		)
		
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
