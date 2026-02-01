from ..common import *

from django.http import JsonResponse


def get_restaurants(request: Any):
	D = [
		{
			'id': 	1,
			'name':	'Example1',
			'lat':	33.645963,
			'lng':	-117.842825,
		},
		{
			'id':		2,
			'name':	'Example2',
			'lat':	33.645958,
			'lng':	-117.842648,
		},
	]

	return JsonResponse({'restaurants': D})
