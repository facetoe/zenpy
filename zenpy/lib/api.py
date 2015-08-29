from zenpy.lib.objects.audit import Audit
from zenpy.lib.objects.events.create import CreateEvent
from zenpy.lib.objects.events.notification import Notification
from zenpy.lib.objects.metadata import Metadata
from zenpy.lib.objects.source import Source
from zenpy.lib.objects.system import System
from zenpy.lib.objects.ticket_audit import TicketAudit
from zenpy.lib.objects.via import Via

__author__ = 'facetoe'
from zenpy.lib.endpoint import Endpoint
from zenpy.lib.util import cached, ApiObjectEncoder
from zenpy.lib.objects.brand import Brand
from zenpy.lib.objects.group import Group
from zenpy.lib.objects.organization import Organization
from zenpy.lib.objects.ticket import Ticket
from zenpy.lib.objects.topic import Topic
from zenpy.lib.objects.user import User
from zenpy.lib.objects.attachment import Attachment
from zenpy.lib.objects.comment import Comment
from zenpy.lib.objects.thumbnail import Thumbnail
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

	user_cache = LRUCache(maxsize=200)
	organization_cache = LRUCache(maxsize=100)
	group_cache = LRUCache(maxsize=100)
	brand_cache = LRUCache(maxsize=100)
	ticket_cache = TTLCache(maxsize=100, ttl=30)
	comment_cache = TTLCache(maxsize=100, ttl=30)

	cache_mapping = {
		'user': user_cache,
		'organization': organization_cache,
		'group': group_cache,
		'brand': brand_cache,
		'ticket': ticket_cache,
		'comment': comment_cache
	}

	class_mapping = {
		'ticket': Ticket,
		'user': User,
		'organization': Organization,
		'group': Group,
		'brand': Brand,
		'topic': Topic,
		'comment': Comment,
		'attachment': Attachment,
		'thumbnail': Thumbnail,
		'metadata': Metadata,
		'system': System,
		'create': CreateEvent,
		'notification': Notification,
		'via': Via,
		'source': Source
	}

	def __init__(self, subdomain, email, token):
		self.email = email
		self.token = token
		self.subdomain = subdomain
		self.protocol = 'https'
		self.version = 'v2'
		self.base_url = self._get_url()

	def get_items(self, endpoint, object_type, kwargs):
		if 'id' in kwargs:
			return self.get_item(kwargs['id'], endpoint, object_type, True)

		if 'ids' in kwargs:
			cached_objects = []
			for id in kwargs['ids']:
				obj = self.query_cache(object_type, id)
				if obj:
					cached_objects.append(obj)
				else:
					return self.get_paginated(endpoint, kwargs, object_type)
			return cached_objects

		return self.get_paginated(endpoint, kwargs, object_type)

	def get_paginated(self, endpoint, kwargs, object_type):
		_json = self._query(endpoint=endpoint(**kwargs))
		self.update_caches(_json)
		return ResultGenerator(self, object_type, _json)

	def get_item(self, id, endpoint, object_type, sideload=True):

		# If this is called with an id from a subclass
		# the cache won't be checked by the decorator, so check it explicitly.
		cached_item = self.query_cache(object_type, id)
		if cached_item:
			return cached_item

		_json = self._query(endpoint=endpoint(id=id, sideload=sideload))

		# Executing a secondary endpoint with an ID will lead here.
		# If the result is paginated return a generator
		if 'next_page' in _json:
			return ResultGenerator(self, object_type, _json)
		else:
			self.update_caches(_json)
			clazz = self.class_for_type(object_type)
			return self._object_from_json(clazz, _json[object_type])

	@cached(user_cache)
	def get_user(self, id, endpoint=Endpoint().users, object_type='user'):
		return self.get_item(id, endpoint, object_type, sideload=True)

	@cached(organization_cache)
	def get_organization(self, id, endpoint=Endpoint().organizations, object_type='organization'):
		return self.get_item(id, endpoint, object_type, sideload=True)

	@cached(group_cache)
	def get_group(self, id, endpoint=Endpoint().groups, object_type='group'):
		return self.get_item(id, endpoint, object_type, sideload=True)

	@cached(brand_cache)
	def get_brand(self, id, endpoint=Endpoint().brands, object_type='brand'):
		return self.get_item(id, endpoint, object_type, sideload=True)

	def get_attachments(self, attachments):
		clazz = self.class_for_type('attachment')
		for attachment in attachments:
			yield self._object_from_json(clazz, attachment)

	def get_events(self, events):
		for event in events:
			yield self.object_from_json(event['type'].lower(), event)

	def get_thumbnails(self, thumbnails):
		for thumbnail in thumbnails:
			yield self.object_from_json('thumbnail', thumbnail)

	def _cache_item(self, cache, item_json, item_type):
		cache[item_json['id']] = self._object_from_json(item_type, item_json)

	def _query(self, endpoint):
		response = self.get(self._get_url(endpoint=endpoint))
		return response.json()

	def create_object(self, endpoint, object):
		_json = self._post(self._get_url(endpoint=endpoint), payload=dict(ticket=vars(object)))
		return _json

	def delete_items(self, endpoint, items):
		if isinstance(items,list) or isinstance(items, ResultGenerator):
			ids = [i.id for i in items]
			response = self._delete(self._get_url(endpoint=endpoint(destroy_ids=ids, sideload=False)))
		else:
			response = self._delete(self._get_url(endpoint=endpoint(id=items.id, sideload=False)))
		if response.status_code != 200:
			response.raise_for_status

	def _post(self, url, payload):
		log.debug("POST: " + url)
		payload = json.loads(json.dumps(payload, cls=ApiObjectEncoder))
		headers = {'Content-type': 'application/json'}
		response = requests.post(url, auth=self._get_auth(), json=payload, headers=headers)
		response_json = response.json()
		return self.build_audit(response_json)

	def build_audit(self, response_json):
		ticket_audit = TicketAudit()
		ticket_audit.ticket = self._object_from_json(Ticket, response_json['ticket'])
		ticket_audit.audit = self._object_from_json(Audit, response_json['audit'])
		return ticket_audit

	def _delete(self, url):
		log.debug("DELETE: " + url)
		response = requests.delete(url, auth=self._get_auth())
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

	def class_for_type(self, object_type):
		if object_type not in self.class_mapping:
			raise Exception("Unknown object_type: " + str(object_type))
		else:
			return self.class_mapping[object_type]

	def object_from_json(self, object_type, object_json):
		obj = self.class_for_type(object_type)
		return self._object_from_json(obj, object_json)

	def _object_from_json(self, object_type, object_json):
		obj = object_type(api=self)
		for key, value in object_json.iteritems():
			if key in ('results', 'metadata', 'from'):
				key = '_%s' % key
			setattr(obj, key, value)
		return obj

	def _get_url(self, endpoint=''):
		return "%(protocol)s://%(subdomain)s.zendesk.com/api/%(version)s/" % self.__dict__ + endpoint

	def _get_auth(self):
		return self.email + '/token', self.token

	def query_cache(self, object_type, id):
		cache = self.cache_mapping[object_type]
		if id in cache:
			log.debug("Cache HIT: [%s %s]" % (object_type.capitalize(), id))
			return cache[id]
		else:
			log.debug('Cache MISS: [%s %s]' % (object_type.capitalize(), id))

	def add_to_cache(self, object_type, object_json):
		cache = self.cache_mapping[object_type]
		clazz = self.class_for_type(object_type)
		multiple_key = object_type + 's'

		if object_type in object_json:
			obj = object_json[object_type]
			log.debug("Caching: [%s %s]" % (object_type.capitalize(), obj['id']))
			self._cache_item(cache, obj, clazz)

		elif multiple_key in object_json:
			objects = object_json[multiple_key]
			log.debug("Caching %s %s " % (len(objects), multiple_key.capitalize()))
			for obj in object_json[multiple_key]:
				self._cache_item(cache, obj, clazz)

	def update_caches(self, _json):
		if 'results' in _json:
			self.cache_search_results(_json)
		else:
			for object_type in self.cache_mapping.keys():
				self.add_to_cache(object_type, _json)

	def cache_search_results(self, _json):
		results = _json['results']
		log.debug("Caching %s search results" % len(results))
		for result in results:
			object_type = result['result_type']
			clazz = self.class_mapping[object_type]
			cache = self.cache_mapping[object_type]
			self._cache_item(cache, result, clazz)


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

	def __call__(self, **kwargs):
		return self.get_items(self.endpoint, self.object_type, kwargs)

	def organizations(self, **kwargs):
		return self.get_items(self.endpoint.organizations, 'ticket', kwargs)

	def recent(self, **kwargs):
		return self.get_items(self.endpoint.recent, 'ticket', kwargs)

	def comments(self, **kwargs):
		return self.get_items(self.endpoint.comments, 'comment', kwargs)

	def create(self, ticket):
		return self.create_object(self.endpoint(sideload=False), ticket)

	def delete(self, items):
		return self.delete_items(self.endpoint, items)


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

		self.search = SimpleApi(subdomain,
		                        email,
		                        token,
		                        endpoint=endpoint.search,
		                        object_type='results')

		self.topics = SimpleApi(subdomain,
		                        email,
		                        token,
		                        endpoint=endpoint.topics,
		                        object_type='topic')

		self.attachments = SimpleApi(subdomain,
		                             email,
		                             token,
		                             endpoint=endpoint.attachments,
		                             object_type='attachment')


class ResultGenerator(object):
	api = None
	_json = None
	position = 0

	endpoint_mapping = {
		'user': 'users',
		'ticket': 'tickets',
		'group': 'groups',
		'results': 'results',
		'organization': 'organizations',
		'topic': 'topics',
		'comment': 'comments'
	}

	def __init__(self, api, result_key, _json):
		self.api = api
		self._json = _json
		self.result_key = self.endpoint_mapping[result_key]
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
		return self.api.object_from_json(object_type, item_json)
