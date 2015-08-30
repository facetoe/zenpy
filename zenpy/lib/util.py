import logging

__author__ = 'facetoe'
log = logging.getLogger(__name__)


def cached(cache):
	"""
	Decorator for caching return values.
	:param cache: The cache for this decorated method
	"""

	def outer(func):
		def inner(*args):
			_id = args[1]
			if _id in cache:
				value = cache[_id]
				log.debug("Cache HIT: [%s %s]" % (value.__class__.__name__, _id))
				return value
			else:
				value = func(*args)
				log.debug("Cache MISS: [%s %s]" % (value.__class__.__name__, _id))
				cache[_id] = value
				return value

		return inner

	return outer
