import collections
from json import JSONEncoder
import logging

__author__ = 'facetoe'
log = logging.getLogger(__name__)


class ApiObjectEncoder(JSONEncoder):
	""" Class for encoding API objects"""
	def default(self, o):
		return o.to_dict()


def cached(cache):
	"""
	Decorator for caching return values.
	:param cache: The cache for this decorated method
	"""
	def outer(func):
		def inner(*args):
			if not isinstance(args, collections.Hashable):
				log.warn("Unhashable type passed to cache")
				return func(*args)
			if args in cache:
				return cache[args]
			else:
				value = func(*args)
				cache.update([((value.api, value.id), value)])
				return value

		return inner

	return outer