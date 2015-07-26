__author__ = 'facetoe'
from zenpy.lib.endpoint import Endpoint
from zenpy.lib.util import cached, ApiObjectEncoder
from zenpy.lib.objects.brand import Brand
from zenpy.lib.objects.group import Group
from zenpy.lib.objects.organization import Organization
from zenpy.lib.objects.result import Result
from zenpy.lib.objects.ticket import Ticket
from zenpy.lib.objects.topic import Topic
from zenpy.lib.objects.user import User
from cachetools import LRUCache, TTLCache
import json
import requests
import logging

log = logging.getLogger(__name__)

class Api(object):
	email = None
	token = None
	subdomain = None
	protocol = None
	version = None
	base_url = None
	endpoint = Endpoint()

	user_cache = LRUCache(maxsize=100)
	organization_cache = LRUCache(maxsize=100)
	group_cache = LRUCache(maxsize=100)
	brand_cache = LRUCache(maxsize=100)
	ticket_cache = TTLCache(maxsize=100, ttl=30)

	def __init__(self, subdomain, email, token):
		self.email = email
		self.token = token
		self.subdomain = subdomain
		self.protocol = 'https'
		self.version = 'v2'
		self.base_url = self._get_url()

	def invalidate_caches(self):
		self.user_cache.clear()
		self.organization_cache.clear()
		self.group_cache.clear()
		self.brand_cache.clear()

	def search(self, **kwargs):
		_json = self._query(endpoint=self.endpoint.search(**kwargs))
		return self._object_from_json(Result, _json)

	def users(self, **kwargs):
		if 'id' in kwargs:
			return self.get_user(kwargs['id'])

		_json = self._query(endpoint=self.endpoint.users(**kwargs))
		return ResultGenerator(self, 'users', _json)

	def tickets(self, **kwargs):
		if 'id' in kwargs:
			return self.get_ticket(kwargs['id'])

		_json = self._query(endpoint=self.endpoint.tickets(**kwargs))
		return ResultGenerator(self, 'tickets', _json)

	def groups(self, **kwargs):
		if 'id' in kwargs:
			return self.get_group(kwargs['id'])

		_json = self._query(endpoint=self.endpoint.groups(**kwargs))
		self.update_caches(_json)
		return ResultGenerator(self, 'groups', _json)

	def result_generator(self, _json, result_key='results'):
		return ResultGenerator(self, result_key, _json)

	@cached(user_cache)
	def get_user(self, user_id, sideload=False):
		_json = self._query(endpoint=self.endpoint.users(id=user_id, sideload=sideload))
		self.update_caches(_json)
		return self._object_from_json(User, _json['user'])

	def cache_user(self, user_json):
		self._cache_item(self.user_cache, user_json, User)

	@cached(ticket_cache)
	def get_ticket(self, ticket_id):
		_json = self._query(endpoint=self.endpoint.tickets(id=ticket_id, sideload='users'))
		self.update_caches(_json)
		return self._object_from_json(Ticket, _json['ticket'])

	def cache_ticket(self, ticket_json):
		self._cache_item(self.ticket_cache, ticket_json, Ticket)

	@cached(organization_cache)
	def get_organization(self, organization_id, sideload=False):
		_json = self._query(endpoint=self.endpoint.organizations(id=organization_id, sideload=sideload))
		self.update_caches(_json)
		return self._object_from_json(Organization, _json['organization'])

	def cache_organization(self, organization_json):
		self._cache_item(self.organization_cache, organization_json, Organization)

	@cached(group_cache)
	def get_group(self, group_id, sideload=False):
		_json = self._query(endpoint=self.endpoint.groups(group_id, sideload=sideload))
		self.update_caches(_json)
		return self._object_from_json(Group, _json['group'])

	def cache_group(self, group_json):
		self._cache_item(self.organization_cache, group_json, Group)

	@cached(brand_cache)
	def get_brand(self, brand_id):
		_json = self._query(endpoint='brands/%s.json' % brand_id)
		self.update_caches(_json)
		return self._object_from_json(Brand, _json['brand'])

	def cache_brand(self, brand_json):
		self._cache_item(self.organization_cache, brand_json, Brand)

	def get_topic(self, brand_id):
		_json = self._query(endpoint='topics/%s.json' % brand_id)
		self.update_caches(_json)
		return self._object_from_json(Topic, _json['topic'])

	def _cache_item(self, cache, item_json, item_type):
		cache.update([((self, item_json['id']), self._object_from_json(item_type, item_json))])

	def _query(self, endpoint):
		response = self.get(self._get_url(endpoint=endpoint))
		return response.json()

	def post_ticket(self, ticket):
		_json = self._post(self._get_url(endpoint='tickets.json'), payload=dict(ticket=vars(ticket)))
		return _json

	def _post(self, url, payload):
		log.debug("POST: " + url)
		payload = json.loads(json.dumps(payload, cls=ApiObjectEncoder))
		headers = {'Content-type': 'application/json'}
		response = requests.post(url, auth=self._get_auth(), json=payload, headers=headers)
		return response

	def get(self, url, stream=False):
		log.debug("GET: " + url)
		response = requests.get(url, auth=self._get_auth(), stream=stream)
		if response.status_code == 422:
			raise Exception("Api rejected query: " + url)
		elif response.status_code == 404 and 'application/json' in response.headers['content-type']:
			raise Exception(response.json()['description'])
		elif response.status_code != 200:
			response.raise_for_status()
		else:
			return response

	def object_from_json(self, object_type, object_json):
		if object_type == 'ticket':
			return self._object_from_json(Ticket, object_json)
		elif object_type == 'user':
			return self._object_from_json(User, object_json)
		elif object_type == 'organization':
			return self._object_from_json(Organization, object_json)
		elif object_type == 'group':
			return self._object_from_json(Group, object_json)
		elif object_type == 'brand':
			return self._object_from_json(Brand, object_json)
		elif object_type == 'topic':
			return self._object_from_json(Topic, object_json)
		else:
			raise Exception("Unknown object_type: " + object_type)

	def _object_from_json(self, object_type, object_json):
		obj = object_type(api=self)
		for key, value in object_json.iteritems():
			if key == 'results':
				key = '_results'
			setattr(obj, key, value)
		return obj

	def _get_url(self, endpoint=''):
		return "%(protocol)s://%(subdomain)s.zendesk.com/api/%(version)s/" % self.__dict__ + endpoint

	def _get_auth(self):
		return self.email + '/token', self.token

	def update_caches(self, _json):
		if 'users' in _json:
			users = _json['users']
			log.debug("Caching %s users" % len(users))
			for user in users:
				self.cache_user(user)
		if 'organizations' in _json:
			orgs = _json['organizations']
			log.debug("Caching %s organizations" % len(orgs))
			for org in orgs:
				self.cache_organization(org)
		if 'groups' in _json:
			groups = _json['groups']
			log.debug("Caching %s groups" % len(groups))
			for group in groups:
				self.cache_group(group)


class ResultGenerator(object):
	api = None
	_json = None
	position = 0

	def __init__(self, api, result_key, _json):
		self.api = api
		self._json = _json
		self.result_key = result_key
		if result_key == 'results':  # hack because of results array in search
			self.values = _json['_results']
		else:
			self.values = _json[result_key]

	def __iter__(self):
		return self

	# Python 3 compatibility
	def __next__(self):
		return self.next()

	def get_as_json(self, url):
		log.debug("GENERATOR: " + url)
		response = self.api.get(url)
		return response.json()

	def next(self):
		# Pagination
		if self.position >= len(self.values):
			if self._json.get('next_page'):
				self._json = self.get_as_json(self._json.get('next_page'))
				self.values = self._json[self.result_key]
				self.position = 0
			else:
				raise StopIteration()

		if not self.values:
			raise StopIteration()

		item_json = self.values[self.position]
		self.api.update_caches(item_json)
		self.position += 1
		if 'result_type' in item_json:
			object_type = item_json.pop('result_type')
		else:
			object_type = self.result_key[:-1]
		return self.api.object_from_json(object_type, item_json)


