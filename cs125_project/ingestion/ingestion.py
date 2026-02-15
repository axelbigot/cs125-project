import requests
import json
import os
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

import time
import zipfile

from pathlib import Path
from dotenv import load_dotenv
from math import cos, pi, ceil, sqrt
from datetime import datetime
from tqdm import tqdm
from typing import *

from included_types import *
from fields import *


load_dotenv()

API_KEY = os.getenv('GOOGLE_API_KEY')

class RawDataRepository:
	def __init__(self, 
		dir: os.PathLike = None, 
		radius_meters: float = 20000, 
		center_lat: float = 33.645963, 
		center_lng: float = -117.842825,
		grid_sub_radius_meters: float = 500
	):
		if dir is None:
			dir = Path('data') / f'{self.__class__.__name__}_{int(radius_meters)}_{int(center_lat)}_{int(center_lng)}'
		dir = Path(dir)

		dir.parent.mkdir(parents=True, exist_ok=True)
		self.is_new = False
		

		zip_path = Path(f'{dir.name}.zip')
		if zip_path.exists() and not dir.exists():
			logging.info(f'Found compressed repository at {zip_path}. Extracting to {dir.parent}')
			with zipfile.ZipFile(zip_path, 'r') as z:
				z.extractall(dir.parent)

			self.is_new = True
		
		dir.mkdir(parents=True, exist_ok=True)

		self._stats_path = dir / 'stats.json'
		self._step_path = dir / 'step.json'
		self._places_dir = dir / 'places'

		completed_at = dir / 'completed_at.txt'
		if completed_at.exists():
			with open(completed_at, 'r') as f:
				timestamp = f.read()
		else:
			self.is_new = True

			grid = self._create_grid(radius_meters, center_lat, center_lng, dim=self._grid_dim(radius_meters, grid_sub_radius_meters))
			self._generate_recursive(self._places_dir, grid)

			timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			with open(completed_at, 'w') as f:
				f.write(timestamp)

			logging.info(f'Compressing {dir} to {dir / zip_path}')
			with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
				for p in dir.rglob('*'):
					if p.is_file():
						z.write(p, dir.name / p.relative_to(dir))

			zip_path.rename(str((dir / zip_path.name)))
			logging.info(f'Compressed {dir} to {zip_path}')

		if not self._places_dir.exists():
			self.place_files = []
		else:
			self.place_files = sorted(p for p in self._places_dir.rglob('*') if p.is_file())

		unique_places, _, _, efficiency = self._get_stats()

		logging.info(f'{self.__class__.__name__} with (radius_meters=={radius_meters},center_lat~={center_lat},center_lng~={center_lng} built at location {dir} at time {timestamp} with {unique_places} unique places retrived with %{(efficiency*100):0.2f} API efficiency')

	def __getitem__(self, index):
		if isinstance(index, slice):
			return [json.load(open(p, 'r')) for p in self.place_files[index]]
		
		with open(self.place_files[index], 'r') as f:
			return json.load(f)

	def _generate_recursive(self, 
		dir: os.PathLike, 
		grid: list[tuple[float, float, float]],
		n_places_recurse: int = 20,
		max_depth: int = 4, 
		curr_depth: int = 1
	):
		if curr_depth == 1:
			step_path = self._step_path
			step_path.touch(exist_ok=True)

			with open(step_path, 'r') as f:
				content = f.read()
				step = int(content) if content else 0

			logging.info(f'Starting from cell {step}/{len(grid)}')
		else:
			step = 0

		for cell in tqdm(grid[step:], desc=f'Building {dir}'):
			radius, center_lat, center_lng = cell

			n_queried = self._generate(dir, radius, center_lat, center_lng)
			
			if n_queried >= n_places_recurse:
				if curr_depth >= max_depth:
					logging.warning(f'Max depth ({max_depth}) reached and still getting >= {n_places_recurse} results! Some places may be excluded')
					continue

				subgrid = self._create_grid(radius, center_lat, center_lng)
				self._generate_recursive(dir, subgrid, curr_depth=curr_depth + 1)
			
			if curr_depth == 1:
				step += 1
				with open(step_path, 'w') as f:
					f.write(str(step))

	def _generate(self, dir: os.PathLike, radius: float, center_lat: float, center_lng: float) -> int:
		dir = Path(dir)
		dir.mkdir(parents=True, exist_ok=True)

		time.sleep(0.5)
		places = self._fetch_places(radius, center_lat, center_lng, fields=FIELDS, included_types=INCLUDED_TYPES)

		unique_places = 0
		for place in places:
			pid = str(place['id'])
			ppath = dir / f'{pid}.json'

			if ppath.exists():
				continue # duplicate place

			with open(ppath, 'w') as f:
				f.write(json.dumps(place, indent=1))

			unique_places += 1

		tot_unique_places, tot_queried_places, tot_requests, _ = self._get_stats()
		self._set_stats(tot_unique_places + unique_places, tot_queried_places + len(places), tot_requests + 1)

		return len(places)

	def _fetch_places(self, 
		radius: float, 
		center_lat: float, 
		center_lng: float,
		fields: list[str] = None,
		included_types: list[str] = None
	) -> list[Any]:
		headers = {
			'Content-Type': 'application/json',
			'X-Goog-Api-Key': API_KEY,
			'X-Goog-FieldMask': ','.join(fields) if fields is not None else '*'
		}

		payload = {
			'includedTypes': included_types,
			'locationRestriction': {
				'circle': {
					'center': {
						'latitude': center_lat,
						'longitude': center_lng,
					},
					'radius': radius
				}
			}
		}

		url = 'https://places.googleapis.com/v1/places:searchNearby'

		for attempt in range(5):
			response = requests.post(url, headers=headers, data=json.dumps(payload))

			if response.status_code == 200:
				break

			if response.status_code in (429, 500, 503):
				time.sleep(2 ** attempt)
				continue

			response.raise_for_status()

		if response.status_code != 200:
			response.raise_for_status()

		result = response.json()
		
		return result.get('places', [])

	def _grid_dim(self, total_radius: float, cell_radius: float) -> int:
		return ceil((total_radius * sqrt(2)) / cell_radius)

	def _create_grid(self,
		total_radius: float, 
		center_lat: float, 
		center_lng: float, 
		dim: int = 3
	) -> list[tuple[float, float, float]]:
		grid = []
		cell_radius = total_radius / dim

		m_per_deg_lat = 111000
		m_per_deg_lng = m_per_deg_lat * cos(center_lat * (pi / 180))
		dlat = (cell_radius * 2) / m_per_deg_lat
		dlng = (cell_radius * 2) / m_per_deg_lng

		off_lat = -(cell_radius * dim) / m_per_deg_lat + (dlat / 2)
		off_lng = -(cell_radius * dim) / m_per_deg_lng + (dlng / 2)

		for i in range(dim):
			for j in range(dim):
				cell_lat = center_lat + off_lat + (i * dlat)
				cell_lng = center_lng + off_lng + (j * dlng)
				
				grid.append((cell_radius, cell_lat, cell_lng))

		return grid
	
	def _set_stats(self, unique_places: int, queried_places: int, requests: int):
		stats = {
			'unique_places': unique_places, 
			'queried_places': queried_places, 
			'requests': requests, 
			'efficiency': (unique_places / queried_places) if queried_places > 0 else 0.00
		}

		with open(self._stats_path, 'w') as f:
			json.dump(stats, f, indent=1)

	def _get_stats(self) -> tuple[int, int, int, float]:
		if not self._stats_path.exists():
			return 0, 0, 0, 0.00
		
		with open(self._stats_path, 'r') as f:
			stats = json.load(f)

		return int(stats.get('unique_places', 0)), int(stats.get('queried_places', 0)), int(stats.get('requests', 0)), float(stats.get('efficiency', 0.00))
