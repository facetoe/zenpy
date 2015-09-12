from time import sleep

__author__ = 'facetoe'

from zenpy.lib.manager import ObjectManager, ApiObjectEncoder
from zenpy.lib.exception import ZenpyException, APIException
from zenpy.lib.endpoint import Endpoint
from zenpy.lib.generator import ResultGenerator

import json
import requests
import logging

log = logging.getLogger(__name__)


class BaseApi(object):
	"""
	Base class for API.
	"""
	email = None
	token = None
	subdomain = None
	protocol = None
	version = None
	base_url = None

	headers = {'Content-type': 'application/json'}

	def __init__(self, subdomain, email, token):
		self.email = email
		self.token = token
		self.subdomain = subdomain
		self.protocol = 'https'
		self.version = 'v2'
		self.base_url = self._get_url()
		self.object_manager = ObjectManager(self)

	def _post(self, url, payload):
		log.debug("POST: " + url)
		payload = json.loads(json.dumps(payload, cls=ApiObjectEncoder))
		response = requests.post(url, auth=self._get_auth(), json=payload, headers=self.headers)
		self._check_and_cache_response(response)
		return self._build_response(response.json())

	def _put(self, url, payload):
		log.debug("PUT: " + url)
		payload = json.loads(json.dumps(payload, cls=ApiObjectEncoder))
		response = requests.put(url, auth=self._get_auth(), json=payload, headers=self.headers)
		return self._check_and_cache_response(response)

	def _delete(self, url, payload=None):
		log.debug("DELETE: " + url)
		if payload:
			response = requests.delete(url, auth=self._get_auth(), json=payload, headers=self.headers)
		else:
			response = requests.delete(url, auth=self._get_auth())
		return self._check_and_cache_response(response)

	def _get(self, url, stream=False):
		log.debug("GET: " + url)
		response = requests.get(url, auth=self._get_auth(), stream=stream)

		# If we are being rate-limited, wait the required period before trying again.
		while 'retry-after' in response.headers and int(response.headers['retry-after']) > 0:
			retry_after_seconds = int(response.headers['retry-after'])
			log.warn(
				"APIRateLimitExceeded - sleeping for requested retry-after period: %s seconds" % retry_after_seconds)
			while retry_after_seconds > 0:
				retry_after_seconds -= 1
				log.debug("APIRateLimitExceeded - sleeping: %s more seconds" % retry_after_seconds)
				sleep(1)
			response = requests.get(url, auth=self._get_auth(), stream=stream)
		return self._check_and_cache_response(response)

	def _get_items(self, endpoint, object_type, kwargs):
		sideload = 'sideload' not in kwargs or ('sideload' in kwargs and kwargs['sideload'])

		# If an ID is present a single object has been requested
		if 'id' in kwargs:
			return self._get_item(kwargs['id'], endpoint, object_type, sideload)

		if 'ids' in kwargs:
			cached_objects = []
			# Check to see if we have all objects in the cache.
			# If we are missing even one we need to request them all again.
			for _id in kwargs['ids']:
				obj = self.object_manager.query_cache(object_type, _id)
				if obj:
					cached_objects.append(obj)
				else:
					return self._get_paginated(endpoint, kwargs, object_type)
			return cached_objects

		return self._get_paginated(endpoint, kwargs, object_type)

	def _get_item(self, _id, endpoint, object_type, sideload=True, skip_cache=False):
		if not skip_cache:
			# Check if we already have this item in the cache
			item = self.object_manager.query_cache(object_type, _id)
			if item:
				return item

		_json = self._query(endpoint=endpoint(id=_id, sideload=sideload))

		# If the result is paginated return a generator
		if 'next_page' in _json:
			return ResultGenerator(self, object_type, _json)
		# Annoyingly, tags is always plural.
		if 'tags' in _json:
			return self.object_manager.object_from_json(object_type, _json[object_type + 's'])
		else:
			return self.object_manager.object_from_json(object_type, _json[object_type])

	def create_items(self, endpoint, items):
		# 'items' is a bit misleading, it's either an object or a list
		if isinstance(items, list) and items:
			first_obj = next((x for x in items))
			object_type = "%ss" % first_obj.__class__.__name__.lower()
			return self._post(self._get_url(
				endpoint=endpoint(
					create_many=True,
					sideload=False)),
				payload={object_type: [vars(i) for i in items]})
		elif items:
			object_type = "%s" % items.__class__.__name__.lower()
			return self._post(self._get_url(
				endpoint=endpoint(
					sideload=False)),
				payload={object_type: vars(items)})

	def update_items(self, endpoint, items):
		if isinstance(items, list) or isinstance(items, ResultGenerator):
			first_obj = next((x for x in items))
			object_type = "%ss" % first_obj.__class__.__name__.lower()
			response = self._put(self._get_url(
				endpoint=endpoint(
					update_many=True,
					sideload=False)),
				payload={object_type: [vars(i) for i in items]})
		else:
			object_type = "%s" % items.__class__.__name__.lower()
			response = self._put(self._get_url(
				endpoint=endpoint(
					id=items.id,
					sideload=False)),
				payload={object_type: vars(items)})

		return self._build_response(response.json())

	def delete_items(self, endpoint, items):
		if (isinstance(items, list) or isinstance(items, ResultGenerator)) and len(items) > 0:
			# Consume the generator here so when we pass it to delete_from_cache
			# there is something to delete.
			items = [i for i in items]
			self._delete(self._get_url(
				endpoint=endpoint(
					destroy_ids=[i.id for i in items],
					sideload=False)))
		elif items:
			self._delete(self._get_url(
				endpoint=endpoint(
					id=items.id,
					sideload=False)))
		else:
			return

		self.object_manager.delete_from_cache(items)

	def _get_paginated(self, endpoint, kwargs, object_type):
		_json = self._query(endpoint=endpoint(**kwargs))
		return ResultGenerator(self, object_type, _json)

	def _query(self, endpoint):
		response = self._get(self._get_url(endpoint=endpoint))
		return response.json()

	def _build_response(self, response_json):
		# When updating and deleting API objects various responses can be returned
		# We can figure out what we have by the keys in the returned JSON
		if 'ticket' and 'audit' in response_json:
			response = self.object_manager.object_from_json('ticket_audit', response_json['ticket_audit'])
		elif 'user' in response_json:
			response = self.object_manager.object_from_json('user', response_json['user'])
		elif 'job_status' in response_json:
			response = self.object_manager.object_from_json('job_status', response_json['job_status'])
		elif 'group' in response_json:
			response = self.object_manager.object_from_json('group', response_json['group'])
		elif 'tags' in response_json:
			return response_json['tags']
		else:
			raise ZenpyException("Unknown Response: " + str(response_json))

		return response

	def _check_and_cache_response(self, response):
		if response.status_code > 299 or response.status_code < 200:
			# Try and get a nice error message
			if 'application/json' in response.headers['content-type']:
				try:
					raise APIException(json.dumps(response.json()))
				except ValueError:
					pass
			# No can do, just raise the correct Exception.
			try:
				response.raise_for_status()
			except requests.exceptions.HTTPError, e:
				raise APIException(e.message)
		else:
			try:
				self.object_manager.update_caches(response.json())
			except ValueError:
				pass
			return response

	def _get_url(self, endpoint=''):
		return "%(protocol)s://%(subdomain)s.zendesk.com/api/%(version)s/" % self.__dict__ + endpoint

	def _get_auth(self):
		return self.email + '/token', self.token


class Api(BaseApi):
	"""
	Add an Endpoint to direct the various operations to the correct API location.
	Also add an object_type to define the type of object this Api returns as
	well as some convenience methods.
	"""

	def __init__(self, subdomain, email, token, endpoint, object_type):
		BaseApi.__init__(self, subdomain, email, token)
		self.endpoint = endpoint
		self.object_type = object_type

	def get_user(self, _id, endpoint=Endpoint().users, object_type='user'):
		return self._get_item(_id, endpoint, object_type, sideload=True)

	def get_comment(self, _id, endpoint=Endpoint().tickets.comments, object_type='comment'):
		return self._get_item(_id, endpoint, object_type, sideload=True)

	def get_organization(self, _id, endpoint=Endpoint().organizations, object_type='organization'):
		return self._get_item(_id, endpoint, object_type, sideload=True)

	def get_group(self, _id, endpoint=Endpoint().groups, object_type='group'):
		return self._get_item(_id, endpoint, object_type, sideload=True)

	def get_brand(self, _id, endpoint=Endpoint().brands, object_type='brand'):
		return self._get_item(_id, endpoint, object_type, sideload=True)

	def get_ticket(self, _id, endpoint=Endpoint().tickets, object_type='ticket', skip_cache=False):
		return self._get_item(_id, endpoint, object_type, sideload=False, skip_cache=skip_cache)


class ModifiableApi(Api):
	"""
	ModifiableApi supports create/update/delete operations
	"""

	def create(self, item):
		return self.create_items(self.endpoint, item)

	def delete(self, items):
		return self.delete_items(self.endpoint, items)

	def update(self, items):
		return self.update_items(self.endpoint, items)


class SimpleApi(Api):
	"""
	A SimpleApi doesn't need any special syntax for the calls or additional methods.
	"""

	def __init__(self, subdomain, email, token, endpoint, object_type):
		BaseApi.__init__(self, subdomain, email, token)
		self.endpoint = endpoint
		self.object_type = object_type

	def __call__(self, **kwargs):
		return self._get_items(self.endpoint, self.object_type, kwargs)


class TaggableApi(Api):
	"""
	TaggableApi supports getting, setting, adding and deleting tags.
	"""

	def __init__(self, subdomain, email, token, endpoint):
		BaseApi.__init__(self, subdomain, email, token)
		self.endpoint = endpoint

	def add_tags(self, id, tags):
		return self._put(self._get_url(
			endpoint=self.endpoint.tags(
				id=id,
				sideload=False)),
			payload={'tags': tags})

	def set_tags(self, id, tags):
		return self._post(self._get_url(
			endpoint=self.endpoint.tags(
				id=id,
				sideload=False)),
			payload={'tags': tags})

	def delete_tags(self, id, tags):
		return self._delete(self._get_url(
			endpoint=self.endpoint.tags(
				id=id,
				sideload=False, )),
			payload={'tags': tags})

	def tags(self, **kwargs):
		return self._get_items(self.endpoint.tags, 'tag', kwargs)


class IncrementalApi(Api):
	"""
	IncrementalApi supports the incremental endpoint.
	"""

	def incremental(self, **kwargs):
		return self._get_items(self.endpoint.incremental, self.object_type, kwargs)


class UserApi(TaggableApi, IncrementalApi, ModifiableApi):
	"""
	The UserApi adds some User specific functionality
	"""

	def __init__(self, subdomain, email, token, endpoint):
		Api.__init__(self, subdomain, email, token, endpoint=endpoint, object_type='user')

	def __call__(self, **kwargs):
		return self._get_items(self.endpoint, self.object_type, kwargs)

	def groups(self, **kwargs):
		return self._get_items(self.endpoint.groups, 'group', kwargs)

	def organizations(self, **kwargs):
		return self._get_items(self.endpoint.organizations, 'organization', kwargs)

	def requested(self, **kwargs):
		return self._get_items(self.endpoint.requested, 'ticket', kwargs)

	def cced(self, **kwargs):
		return self._get_items(self.endpoint.cced, 'ticket', kwargs)

	def assigned(self, **kwargs):
		return self._get_items(self.endpoint.assigned, 'ticket', kwargs)


class OranizationApi(TaggableApi, IncrementalApi, ModifiableApi):
	def __init__(self, subdomain, email, token, endpoint):
		Api.__init__(self, subdomain, email, token, endpoint=endpoint, object_type='organization')

	def __call__(self, **kwargs):
		return self._get_items(self.endpoint, self.object_type, kwargs)


class TicketApi(TaggableApi, IncrementalApi, ModifiableApi):
	"""
	The TicketApi adds some Ticket specific functionality
	"""

	def __init__(self, subdomain, email, token, endpoint):
		Api.__init__(self, subdomain, email, token, endpoint=endpoint, object_type='ticket')

	def __call__(self, **kwargs):
		return self._get_items(self.endpoint, self.object_type, kwargs)

	def organizations(self, **kwargs):
		return self._get_items(self.endpoint.organizations, 'ticket', kwargs)

	def recent(self, **kwargs):
		return self._get_items(self.endpoint.recent, 'ticket', kwargs)

	def comments(self, **kwargs):
		return self._get_items(self.endpoint.comments, 'comment', kwargs)

	def events(self, **kwargs):
		return self._get_items(self.endpoint.events, 'ticket_event', kwargs)

	def audits(self, **kwargs):
		return self._get_items(self.endpoint.audits, 'ticket_audit', kwargs)
