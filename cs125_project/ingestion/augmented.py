from __future__ import annotations
import sqlite3

from sqlite3 import Connection, Cursor
from dataclasses import dataclass
from typing import List, Optional, Any
from tqdm import tqdm

from .ingestion import *


@dataclass
class Place:
	id: str
	name: Optional[str]
	main_type: Optional[str]
	lat: Optional[float]
	lng: Optional[float]
	rating: Optional[float]
	rating_count: Optional[int]
	price_level: Optional[int]
	website: Optional[str]
	phone: Optional[str]
	address: Optional[str]
	timezone_offset: Optional[int]
	takeout: Optional[bool]
	delivery: Optional[bool]
	dine_in: Optional[bool]
	outdoor_seating: Optional[bool]
	restroom: Optional[bool]
	free_parking: Optional[bool]
	wheelchair_accessible: Optional[bool]
	human_summary: Optional[str]
	ai_summary: Optional[str]
	review_summary: Optional[str]
	directions_uri: Optional[str]
	photos_uri: Optional[str]
	reviews_uri: Optional[str]
	types: Optional[List[str]]
	hours: Optional[Any]

class AugmentedPlacesRepository:
	def __init__(self, conn_loc: str = 'places.db', raw_data: RawDataRepository = None, force_migrate: bool = False):
		self._conn_loc = conn_loc

		if raw_data is None:
			raw_data = RawDataRepository()

		with self._conn() as conn:
			self._create_tables(conn)

			if raw_data.is_new or force_migrate:
				self._migrate_raw(conn, raw_data)

	def query_builder(self) -> PlaceQueryBuilder:
		return PlaceQueryBuilder(self)

	def all(self, limit: int = None) -> List[Place]:
		with self._conn() as conn:
			cursor = conn.cursor()

			if limit is None:
				cursor.execute('SELECT * FROM places')
			else:
				cursor.execute(f'SELECT * FROM places LIMIT {limit}')

			rows = cursor.fetchall()
			return self._rows2places(rows, cursor.description)
		
	def get_by_text_relevance(self, tokens: list[str], limit: int = 20) -> List[Place]:
		with self._conn() as conn:
			cursor = conn.cursor()

			quoted = [f'"{t}"' for t in tokens]
			query = " OR ".join(quoted)
			
			cursor.execute("""
				SELECT p.*
				FROM places p
				JOIN places_fts ON p.rowid = places_fts.rowid
				WHERE places_fts MATCH ?
				ORDER BY bm25(places_fts, 5.0, 2.0, 1.0, 1.0) ASC
				LIMIT ?
			""", (query, limit))

			rows = cursor.fetchall()
			return self._rows2places(rows, cursor.description)

	def _rows2places(self, 
		rows: list[Any],
		desc: tuple[tuple[str, None, None, None, None, None, None], ...]
	) -> List[Place]:
		cols = [col[0] for col in desc]
		places = []

		for row in rows:
			row_dict = dict(zip(cols, row))
			row_dict['types'] = json.loads(row_dict['types']) if row_dict.get('types') else None
			row_dict['hours'] = json.loads(row_dict['hours']) if row_dict.get('hours') else None

			pls = ['PRICE_LEVEL_FREE', 
            'PRICE_LEVEL_INEXPENSIVE', 
            'PRICE_LEVEL_MODERATE', 
            'PRICE_LEVEL_EXPENSIVE', 
            'PRICE_LEVEL_VERY_EXPENSIVE']
			if row_dict['price_level'] in pls:
				pl = pls.index(row_dict['price_level'])
			else:
				pl = None
			
			row_dict['price_level'] = pl

			places.append(Place(**row_dict))

		return places

	def _conn(self) -> sqlite3.Connection:
		return sqlite3.connect(self._conn_loc)

	def _migrate_raw(self, conn: Connection, raw_data: RawDataRepository):
		cursor = conn.cursor()

		logging.info(f'Wiping places table')

		cursor.execute('DELETE FROM places')
		cursor.execute('DELETE FROM places_fts')

		conn.commit()

		insert_sql = """
			INSERT INTO places (
				id, name, main_type, lat, lng, rating, rating_count, price_level,
				website, phone, address, timezone_offset, takeout, delivery, dine_in,
				outdoor_seating, restroom, free_parking, wheelchair_accessible,
				human_summary, ai_summary, review_summary, directions_uri,
				photos_uri, reviews_uri, types, hours
      ) VALUES (
				:id, :name, :main_type, :lat, :lng, :rating, :rating_count, :price_level,
				:website, :phone, :address, :timezone_offset, :takeout, :delivery, :dine_in,
				:outdoor_seating, :restroom, :free_parking, :wheelchair_accessible,
				:human_summary, :ai_summary, :review_summary, :directions_uri,
				:photos_uri, :reviews_uri, :types, :hours
      )"""

		for place in tqdm(raw_data, desc='Migrating'):
			p = self._massage(place)

			p['types'] = json.dumps(p['types']) if p['types'] is not None else None
			p['hours'] = json.dumps(p['hours']) if p['hours'] is not None else None

			cursor.execute(insert_sql, p)
		
		conn.commit()

		cursor.execute("""
			INSERT INTO places_fts(rowid, id, name, human_summary, ai_summary, review_summary)
			SELECT rowid, id, name, human_summary, ai_summary, review_summary
			FROM places;
		""")

		conn.commit()

	def _create_tables(self, conn: Connection):
		cursor = conn.cursor()

		cursor.execute("""
			CREATE TABLE IF NOT EXISTS places (
								 id TEXT PRIMARY KEY,
								 name TEXT,
								 main_type TEXT,
								 lat REAL,
								 lng REAL,
								 rating REAL,
								 rating_count INTEGER,
								 price_level INTEGER,
								 website TEXT,
								 phone TEXT,
								 address TEXT,
								 timezone_offset INTEGER,
								 takeout BOOLEAN,
								 delivery BOOLEAN,
								 dine_in BOOLEAN,
								 outdoor_seating BOOLEAN,
								 restroom BOOLEAN,
								 free_parking BOOLEAN,
								 wheelchair_accessible BOOLEAN,
								 human_summary TEXT,
								 ai_summary TEXT,
								 review_summary TEXT,
								 directions_uri TEXT,
								 photos_uri TEXT,
								 reviews_uri TEXT,
								 types TEXT,
								 hours TEXT
		  )""")
		
		cursor.execute("""
			CREATE VIRTUAL TABLE IF NOT EXISTS places_fts
								 USING fts5(
								 	id UNINDEXED,
								 	name,
								 	human_summary,
								 	ai_summary,
								 	review_summary,
								 	content='places',
								 	content_rowid='rowid'
			)""")
		
		conn.commit()

	def _massage(self, place):
		filtered = {
			'id': self._get(place, 'id'),
			'types': self._get(place, 'types'),
			'main_type': self._get(place, 'primaryType'),
			'phone': self._get(place, 'nationalPhoneNumber'),
			'address': self._get(place, 'formattedAddress'),
			'lat': self._get(place, 'location', 'latitude'),
			'lng': self._get(place, 'location', 'longitude'),
			'rating': self._get(place, 'rating'),
			'goog_uri': self._get(place, 'googleMapsUri'),
			'website': self._get(place, 'websiteUri'),
			'hours': self._get(place, 'regularOpeningHours', 'periods'),
			'timezone_offset': self._get(place, 'utcOffsetMinutes'),
			'price_level': self._get(place, 'priceLevel'),
			'rating_count': self._get(place, 'userRatingCount'),
			'name': self._get(place, 'displayName', 'text'),
			'label': self._get(place, 'primaryTypeDisplayName', 'text'),
			'takeout': self._get(place, 'takeout'),
			'delivery': self._get(place, 'delivery'),
			'dine_in': self._get(place, 'dineIn'),
			'outdoor_seating': self._get(place, 'outdoorSeating'),
			'restroom': self._get(place, 'restroom'),
			'free_parking': (
				self._get(place, 'parkingOptions', 'freeParkingLot') 
				or self._get(place, 'parkingOptions', 'freeStreetParking')
			),
			'wheelchair_accessible': (
				self._get(place, 'accessibilityOptions', 'wheelchairAccessibleParking') 
				and self._get(place, 'accessibilityOptions', 'wheelchairAccessibleEntrance')
			),
			'human_summary': self._get(place, 'editorialSummary', 'text'),
			'ai_summary': self._get(place, 'generativeSummary', 'overview', 'text'),
			'review_summary': self._get(place, 'reviewSummary', 'text', 'text'),
			'reviews': [
				{
					'text': self._get(r, 'text', 'text'),
					'time': self._get(r, 'publishTime'),
					'rating': self._get(r, 'rating')
				} for r in self._get(place, 'reviews', default=[])[:5]
			],
			'directions_uri': self._get(place, 'googleMapsLinks', 'directionsUri'),
			'photos_uri': self._get(place, 'googleMapsLinks', 'photosUri'),
			'reviews_uri': self._get(place, 'googleMapsLinks', 'reviewsUri'),
		}

		return filtered

	def _get(self, obj, *keys, default=None):
		for k in keys:
			if obj is None:
				return default
			obj = obj.get(k, default)
		return obj

class PlaceQueryBuilder:
	def __init__(self, repo: AugmentedPlacesRepository):
		self._repo = repo
		self._joins = []
		self._where = []
		self._params = []
		self._order = []
		self._limit = None

	def within_radius(self, meters: float, lat: float, lng: float) -> 'PlaceQueryBuilder':
		dlat = meters / 111000
		dlng = meters / (111000 * cos(lat * (pi / 180)))

		self._where.append(
			'p.lat BETWEEN ? AND ? AND p.lng BETWEEN ? AND ?'
		)

		self._params.extend([
			lat - dlat,
			lat + dlat,
			lng - dlng,
			lng + dlng
		])

		return self
	
	def order_by_text_relevance(self, tokens: list[str]) -> 'PlaceQueryBuilder':
		quoted = [f'"{t}"' for t in tokens]
		query = " OR ".join(quoted)

		if not query:
			return self
		
		self._joins.append(
			'JOIN places_fts ON p.rowid = places_fts.rowid'
		)

		self._where.append('places_fts MATCH ?')
		self._params.append(query)

		self._order.append('bm25(places_fts, 5.0, 2.0, 1.0, 1.0) ASC')
		return self
	
	def select(self, limit: int = 20) -> list[Place]:
		self._limit = limit

		sql = ['SELECT p.* FROM places p']

		if self._joins:
			sql.extend(self._joins)
		
		if self._where:
			sql.append('WHERE ' + ' AND '.join(self._where))
		
		if self._order:
			sql.append('ORDER BY ' + ', '.join(self._order))

		sql.append('LIMIT ?')
		self._params.append(self._limit)

		final_sql = '\n'.join(sql)

		debug_sql = final_sql
		for p in self._params:
			debug_sql = debug_sql.replace('?', repr(p), 1)
		print(debug_sql)

		with self._repo._conn() as conn:
			cursor = conn.cursor()
			cursor.execute(final_sql, self._params)
			rows = cursor.fetchall()

			return self._repo._rows2places(rows, cursor.description)
