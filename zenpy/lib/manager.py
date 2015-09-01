from zenpy.lib.exception import ZenpyException
from zenpy.lib.objects.via import Via
from zenpy.lib.objects.brand import Brand
from zenpy.lib.objects.group import Group
from zenpy.lib.objects.organization import Organization
from zenpy.lib.objects.ticket import Ticket
from zenpy.lib.objects.topic import Topic
from zenpy.lib.objects.user import User
from zenpy.lib.objects.attachment import Attachment
from zenpy.lib.objects.comment import Comment
from zenpy.lib.objects.thumbnail import Thumbnail
from zenpy.lib.objects.audit import Audit
from zenpy.lib.objects.events.create import CreateEvent
from zenpy.lib.objects.events.notification import Notification
from zenpy.lib.objects.job_status import JobStatus
from zenpy.lib.objects.metadata import Metadata
from zenpy.lib.objects.source import Source
from zenpy.lib.objects.system import System

from cachetools import LRUCache, TTLCache
from json import JSONEncoder

import logging

log = logging.getLogger(__name__)

__author__ = 'facetoe'

user_cache = LRUCache(maxsize=200)
organization_cache = LRUCache(maxsize=100)
group_cache = LRUCache(maxsize=100)
brand_cache = LRUCache(maxsize=100)
ticket_cache = TTLCache(maxsize=100, ttl=30)
comment_cache = TTLCache(maxsize=100, ttl=30)

class ApiObjectEncoder(JSONEncoder):
	""" Class for encoding API objects"""

	def default(self, o):
		if hasattr(o, 'to_dict'):
			return o.to_dict()


class ClassManager(object):
	"""
	ClassManager provides methods for converting JSON objects
	to the correct Python ones.
	"""

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
		'source': Source,
		'job_status': JobStatus,
		'audit': Audit
	}

	def __init__(self, api):
		self.api = api

	def object_from_json(self, object_type, object_json):
		obj = self._class_for_type(object_type)
		return self._object_from_json(obj, object_json)

	def _class_for_type(self, object_type):
		if object_type not in self.class_mapping:
			raise ZenpyException("Unknown object_type: " + str(object_type))
		else:
			return self.class_mapping[object_type]

	def _object_from_json(self, object_type, object_json):
		obj = object_type(api=self.api)
		for key, value in object_json.iteritems():
			if key in ('results', 'metadata', 'from'):
				key = '_%s' % key
			setattr(obj, key, value)
		return obj

class ObjectManager(object):
	"""
	The ObjectManager is responsible for maintaining various caches
	and also provides access to the ClassManager
	"""

	skip_cache = ('job_status', 'attachment')

	cache_mapping = {
		'user': user_cache,
		'organization': organization_cache,
		'group': group_cache,
		'brand': brand_cache,
		'ticket': ticket_cache,
		'comment': comment_cache
	}

	def __init__(self, api):
		self.class_manager = ClassManager(api)

	def object_from_json(self, object_type, object_json):
		return self.class_manager.object_from_json(object_type, object_json)

	def delete_from_cache(self, obj):
		if isinstance(obj, list):
			for o in obj:
				self._delete_from_cache(o)
		else:
			self._delete_from_cache(obj)

	def _delete_from_cache(self, obj):
		object_type = obj.__class__.__name__.lower()
		cache = self.cache_mapping[object_type]
		obj = cache.pop(obj.id, None)
		if obj:
			log.debug("Cache RM: [%s %s]" % (object_type.capitalize(), obj.id))

	def query_cache(self, object_type, _id):
		if object_type in self.skip_cache:
			return None

		cache = self.cache_mapping[object_type]
		if _id in cache:
			log.debug("Cache HIT: [%s %s]" % (object_type.capitalize(), _id))
			return cache[_id]
		else:
			log.debug('Cache MISS: [%s %s]' % (object_type.capitalize(), _id))

	def update_caches(self, _json):
		if 'tickets' in _json:
			self._add_to_cache('ticket', _json)
		if 'results' in _json:
			self._cache_search_results(_json)
		else:
			for object_type in self.cache_mapping.keys():
				self._add_to_cache(object_type, _json)

	def _add_to_cache(self, object_type, object_json):
		cache = self.cache_mapping[object_type]
		multiple_key = object_type + 's'
		if object_type in object_json:
			obj = object_json[object_type]
			log.debug("Caching: [%s %s]" % (object_type.capitalize(), obj['id']))
			self._cache_item(cache, obj, object_type)

		elif multiple_key in object_json:
			objects = object_json[multiple_key]
			log.debug("Caching %s %s " % (len(objects), multiple_key.capitalize()))
			for obj in object_json[multiple_key]:
				self._cache_item(cache, obj, object_type)

	def _cache_search_results(self, _json):
		results = _json['results']
		log.debug("Caching %s search results" % len(results))
		for result in results:
			object_type = result['result_type']
			cache = self.cache_mapping[object_type]
			self._cache_item(cache, result, object_type)

	def _cache_item(self, cache, item_json, item_type):
		cache[item_json['id']] = self.object_from_json(item_type, item_json)
