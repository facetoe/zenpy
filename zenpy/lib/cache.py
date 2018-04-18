import logging
from threading import RLock

import cachetools

from zenpy.lib.api_objects import BaseObject
from zenpy.lib.exception import ZenpyCacheException
from zenpy.lib.util import get_object_type

__author__ = 'facetoe'

log = logging.getLogger(__name__)
purge_lock = RLock()

set_lock = RLock()

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

    def purge(self):
        """ Purge the cache of all items. """
        with purge_lock:
            self.cache.clear()

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
        if not issubclass(type(value), BaseObject):
            raise ZenpyCacheException("{} is not a subclass of BaseObject!".format(type(value)))
        with set_lock:
            self.cache[key] = value

    def __delitem__(self, key):
        del self.cache[key]

    def __contains__(self, item):
        return item in self.cache

    def __len__(self):
        return len(self.cache)


# Global dictionary for managing default object caches
cache_mapping = {
    'user': ZenpyCache('LRUCache', maxsize=10000),
    'organization': ZenpyCache('LRUCache', maxsize=10000),
    'group': ZenpyCache('LRUCache', maxsize=10000),
    'brand': ZenpyCache('LRUCache', maxsize=10000),
    'ticket': ZenpyCache('TTLCache', maxsize=10000, ttl=30),
    'request': ZenpyCache('LRUCache', maxsize=10000),
    'ticket_field': ZenpyCache('LRUCache', maxsize=10000),
    'sharing_agreement': ZenpyCache('TTLCache', maxsize=10000, ttl=6000),
    'identity': ZenpyCache('LRUCache', maxsize=10000)
}


def delete_from_cache(to_delete):
    """ Purge one or more items from the relevant caches """
    if not isinstance(to_delete, list):
        to_delete = [to_delete]
    for zenpy_object in to_delete:
        object_type = get_object_type(zenpy_object)
        object_cache = cache_mapping.get(object_type, None)
        if object_cache:
            removed_object = object_cache.pop(zenpy_object.id, None)
            if removed_object:
                log.debug("Cache RM: [%s %s]" % (object_type.capitalize(), zenpy_object.id))


def query_cache_by_object(zenpy_object):
    """ Convenience method for testing. Given an object, return the cached version """
    object_type = get_object_type(zenpy_object)
    cache_key = _cache_key_attribute(object_type)
    return query_cache(object_type, getattr(zenpy_object, cache_key))


def query_cache(object_type, cache_key):
    """ Query the cache for a Zenpy object """
    if object_type not in cache_mapping:
        return None
    cache = cache_mapping[object_type]
    if cache_key in cache:
        log.debug("Cache HIT: [%s %s]" % (object_type.capitalize(), cache_key))
        return cache[cache_key]
    else:
        log.debug('Cache MISS: [%s %s]' % (object_type.capitalize(), cache_key))


def add_to_cache(zenpy_object):
    """ Add a Zenpy object to the relevant cache. If no cache exists for this object nothing is done. """
    object_type = get_object_type(zenpy_object)
    if object_type not in cache_mapping:
        return
    attr_name = _cache_key_attribute(object_type)
    cache_key = getattr(zenpy_object, attr_name)
    log.debug("Caching: [{}({}={})]".format(zenpy_object.__class__.__name__, attr_name, cache_key))
    cache_mapping[object_type][cache_key] = zenpy_object


def purge_cache(object_type):
    """ Purge the named cache of all values. If no cache exists for object_type, nothing is done """
    if object_type in cache_mapping:
        cache = cache_mapping[object_type]
        log.debug("Purging [{}] cache of {} values.".format(object_type, len(cache)))
        cache.purge()


def in_cache(zenpy_object):
    """ Determine whether or not this object is in the cache """
    object_type = get_object_type(zenpy_object)
    cache_key_attr = _cache_key_attribute(object_type)
    return query_cache(object_type, getattr(zenpy_object, cache_key_attr)) is not None


def should_cache(zenpy_object):
    """ Determine whether or not this object should be cached (ie, a cache exists for it's object_type) """
    return get_object_type(zenpy_object) in cache_mapping


def _cache_key_attribute(object_type):
    """ Return the attribute used as the cache_key for a particular object type. """
    # This function used to return the key for objects that are not referenced by id.
    # These objects are no longer cached (UserField, OrganizationalField) and so the
    # function has no purpose anymore. I'm leaving it here in case it comes in handy again
    return 'id'
