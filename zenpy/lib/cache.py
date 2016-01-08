import cachetools

from zenpy.lib.exception import ZenpyCacheException

__author__ = 'facetoe'


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
