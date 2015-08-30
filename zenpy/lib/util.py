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
			id = args[1]
			if id in cache:
				value = cache[id]
				log.debug("Cache HIT: [%s %s]" % (value.__class__.__name__, id))
				return value
			else:
				value = func(*args)
				log.debug("Cache MISS: [%s %s]" % (value.__class__.__name__, id))
				cache[id] = value
				return value

		return inner

	return outer

