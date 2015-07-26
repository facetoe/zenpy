from collections import namedtuple

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


class BaseApi(object):
	email = None
	token = None
	subdomain = None
	protocol = None
	version = None
	base_url = None

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

	def result_generator(self, _json, result_key='results'):
		return ResultGenerator(self, result_key, _json)

	def get_items(self, endpoint, object_type, kwargs):
		if 'id' in kwargs:
			return self.get_item(kwargs['id'], endpoint, object_type, True)

		_json = self._query(endpoint=endpoint(**kwargs))
		self.update_caches(_json)
		return ResultGenerator(self, object_type, _json)

	def get_item(self, id, endpoint, object_type, sideload=False):
		_json = self._query(endpoint=endpoint(id=id, sideload=sideload))

		# Executing a secondary endpoint with an ID will lead here.
		# Just return a generator
		if 'next_page' in _json:
			return self.result_generator(_json, result_key=object_type)
		else:
			self.update_caches(_json)
			clazz = self.class_for_type(object_type)
			return self._object_from_json(clazz, _json[object_type])

	def cache_user(self, user_json):
		self._cache_item(self.user_cache, user_json, User)

	def cache_ticket(self, ticket_json):
		self._cache_item(self.ticket_cache, ticket_json, Ticket)

	def cache_organization(self, organization_json):
		self._cache_item(self.organization_cache, organization_json, Organization)

	def cache_group(self, group_json):
		self._cache_item(self.organization_cache, group_json, Group)

	def cache_brand(self, brand_json):
		self._cache_item(self.organization_cache, brand_json, Brand)

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

	@staticmethod
	def class_for_type(object_type):
		if object_type == 'ticket':
			return Ticket
		elif object_type == 'user':
			return User
		elif object_type == 'organization':
			return Organization
		elif object_type.startswith('group'):
			return Group
		elif object_type == 'brand':
			return Brand
		elif object_type == 'topic':
			return Topic
		else:
			raise Exception("Unknown object_type: " + object_type)

	def objects_from_json(self, object_type, object_json):
		obj = self.class_for_type(object_type)
		return self._object_from_json(obj, object_json)

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


class SimpleApi(BaseApi):
	def __init__(self, subdomain, email, token, endpoint, object_type):
		BaseApi.__init__(self, subdomain, email, token)
		self.endpoint = endpoint
		self.object_type = object_type

	def __call__(self, **kwargs):
		return self.get_items(self.endpoint, self.object_type, kwargs)


class UserApi(BaseApi):
	def __init__(self, subdomain, email, token, endpoint):
		BaseApi.__init__(self, subdomain, email, token)
		self.endpoint = endpoint
		self.object_type = 'user'

	def __call__(self, **kwargs):
		return self.get_items(self.endpoint, self.object_type, kwargs)

	def groups(self, **kwargs):
		return self.get_items(self.endpoint.groups, 'group', kwargs)

	def organizations(self, **kwargs):
		return self.get_items(self.endpoint.organizations, 'organization', kwargs)

	def requested(self, **kwargs):
		return self.get_items(self.endpoint.requested, 'ticket', kwargs)

	def cced(self, **kwargs):
		return self.get_items(self.endpoint.cced, 'ticket', kwargs)

	def assigned(self, **kwargs):
		return self.get_items(self.endpoint.assigned, 'ticket', kwargs)


class TicketApi(BaseApi):
	def __init__(self, subdomain, email, token, endpoint):
		BaseApi.__init__(self, subdomain, email, token)
		self.endpoint = endpoint
		self.object_type = 'ticket'

	def organizations(self, **kwargs):
		return self.get_items(self.endpoint.organizations, 'ticket', kwargs)

	def recent(self, **kwargs):
		return self.get_items(self.endpoint.recent, 'ticket', kwargs)


class Api(BaseApi):
	def __init__(self, subdomain, email, token):
		BaseApi.__init__(self, subdomain, email, token)
		endpoint = Endpoint()
		self.users = UserApi(subdomain,
		                     email,
		                     token,
		                     endpoint=endpoint.users)
		self.groups = SimpleApi(subdomain,
		                        email,
		                        token,
		                        endpoint=endpoint.groups,
		                        object_type='group')

		self.organizations = SimpleApi(subdomain,
		                               email,
		                               token,
		                               endpoint=endpoint.organizations,
		                               object_type='organization')
		self.tickets = TicketApi(subdomain,
		                         email,
		                         token,
		                         endpoint=endpoint.tickets)

	# self.groups = ApiEndpoint(subdomain, email, token, endpoint.groups, 'group')


class ResultGenerator(object):
	api = None
	_json = None
	position = 0

	endpoint_mapping = {
		'user': 'users',
		'ticket': 'tickets',
		'group': 'groups',
		'results': 'results',
		'organization': 'organizations'
	}

	def __init__(self, api, result_key, _json):
		self.api = api
		self._json = _json
		self.result_key = self.endpoint_mapping[result_key]
		if self.result_key == 'results':  # hack because of results array in search
			self.values = _json['_results']
		else:
			self.values = _json[self.result_key]

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
		return self.api.objects_from_json(object_type, item_json)
