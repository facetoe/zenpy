import re

import cachetools
import logging

from zenpy.lib.exception import ZenpyCacheException
from zenpy.lib.util import to_snake_case

__author__ = 'facetoe'

log = logging.getLogger(__name__)


class ZenpyCache(object):
    """
    Wrapper class for the various cachetools caches. Adds ability to change cache implementations
    on the fly and change the maxsize setting.
    """
    AVAILABLE_CACHES = [c for c in dir(cachetools) if c.endswith('Cache') and c != 'Cache']

    def __init__(self, cache_impl, maxsize, **kwargs):
        self.cache = self._get_cache_impl(cache_impl, maxsize, **kwargs)

    def set_cache_impl(self, cache_impl, maxsize, **kwargs):
        """
        Change cache implementation. The contents of the old cache will
        be transferred to the new one.
        :param cache_impl: Name of cache implementation, must exist in AVAILABLE_CACHES
        """
        new_cache = self._get_cache_impl(cache_impl, maxsize, **kwargs)
        self._populate_new_cache(new_cache)
        self.cache = new_cache

    def pop(self, key, default=None):
        return self.cache.pop(key, default)

    def items(self):
        return self.cache.items()

    @property
    def impl_name(self):
        """
        Name of current cache implementation
        """
        return self.cache.__class__.__name__

    @property
    def maxsize(self):
        """
        Current max size
        """
        return self.cache.maxsize

    def set_maxsize(self, maxsize, **kwargs):
        """
        Set maxsize. This involves creating a new cache and transferring the items.
        """
        new_cache = self._get_cache_impl(self.impl_name, maxsize, **kwargs)
        self._populate_new_cache(new_cache)
        self.cache = new_cache

    @property
    def currsize(self):
        return len(self.cache)

    def _populate_new_cache(self, new_cache):
        for key, value in self.cache.items():
            new_cache[key] = value

    def _get_cache_impl(self, cache_impl, maxsize, **kwargs):
        if cache_impl not in self.AVAILABLE_CACHES:
            raise ZenpyCacheException(
                "No such cache: %s, available caches: %s" % (cache_impl, str(self.AVAILABLE_CACHES)))
        return getattr(cachetools, cache_impl)(maxsize, **kwargs)

    def __iter__(self):
        return self.cache.__iter__()

    def __getitem__(self, item):
        return self.cache[item]

    def __setitem__(self, key, value):
        self.cache[key] = value

    def __delitem__(self, key):
        del self.cache[key]

    def __contains__(self, item):
        return item in self.cache


# Global dictionary for managing default object caches
cache_mapping = {
    'user': ZenpyCache('LRUCache', maxsize=10000),
    'organization': ZenpyCache('LRUCache', maxsize=10000),
    'group': ZenpyCache('LRUCache', maxsize=10000),
    'brand': ZenpyCache('LRUCache', maxsize=10000),
    'ticket': ZenpyCache('TTLCache', maxsize=10000, ttl=30),
    'comment': ZenpyCache('LRUCache', maxsize=10000),
    'request': ZenpyCache('LRUCache', maxsize=10000),
    'user_field': ZenpyCache('TTLCache', maxsize=10000, ttl=30),
    'organization_field': ZenpyCache('LRUCache', maxsize=10000),
    'ticket_field': ZenpyCache('LRUCache', maxsize=10000),
    'sharing_agreement': ZenpyCache('TTLCache', maxsize=10000, ttl=6000),
    'identity': ZenpyCache('LRUCache', maxsize=10000)
}


def delete_from_cache(to_delete):
    if isinstance(to_delete, list):
        for zenpy_object in to_delete:
            _delete_from_cache(zenpy_object)
    else:
        _delete_from_cache(to_delete)


def _delete_from_cache(obj):
    object_type = to_snake_case(obj.__class__.__name__)
    if object_type in cache_mapping:
        cache = cache_mapping[object_type]
        obj = cache.pop(obj.id, None)
        if obj:
            log.debug("Cache RM: [%s %s]" % (object_type.capitalize(), obj.id))


def query_cache(object_type, _id):
    if object_type not in cache_mapping:
        return None

    cache = cache_mapping[object_type]
    if _id in cache:
        log.debug("Cache HIT: [%s %s]" % (object_type.capitalize(), _id))
        return cache[_id]
    else:
        log.debug('Cache MISS: [%s %s]' % (object_type.capitalize(), _id))


def add_to_cache(zenpy_object):
    object_type = to_snake_case(zenpy_object.__class__.__name__)
    if object_type not in cache_mapping:
        return
    _cache_item(cache_mapping[object_type], zenpy_object, object_type)


def _cache_item(cache, zenpy_object, object_type):
    identifier = _get_identifier(object_type)
    cache_key = getattr(zenpy_object, identifier)
    log.debug("Caching: {}({}={})".format(zenpy_object.__class__.__name__, identifier, cache_key))
    cache[cache_key] = zenpy_object


def _get_identifier(item_type):
    if item_type in ('user_field', 'organization_field'):
        key = 'key'
    else:
        key = 'id'
    return key
