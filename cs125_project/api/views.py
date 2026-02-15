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
		raw_recommendations = get_restaurant_recommendations(request_obj)
		
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
			location = place.get('geometry', {}).get('location', {})
			formatted_place = {
				'id': place.get('place_id', idx),
				'name': place.get('name', 'Unknown'),
				'lat': location.get('lat', 0),
				'lng': location.get('lng', 0),
				'rating': place.get('rating', 0),
				'price': '$' * (place.get('price_level', 0) or 0),
				'type': ', '.join(place.get('types', [])[:2]) if place.get('types') else 'Restaurant',
				'vicinity': place.get('vicinity', ''),
				'image': place.get('photos', [{}])[0].get('photo_reference', '') if place.get('photos') else '',
			}
			formatted_restaurants.append(formatted_place)
		
		return JsonResponse({'restaurants': formatted_restaurants})
	
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)
