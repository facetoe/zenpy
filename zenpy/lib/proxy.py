try:
    from UserDict import UserDict
except ImportError:
    from collections import UserDict


class ProxyDict(UserDict):
    """
    Proxy for dict, records when the dictionary has been modified.
    """

    def __init__(self, *args, **kwargs):
        super(ProxyDict, self).__init__(*args, **kwargs)
        self.data.update(*args, **kwargs)
        self._dirty = False

    def update(self, *args, **kwargs):
        self.data.update(*args, **kwargs)
        self._dirty = True

    def pop(self, key, default=None):
        self.data.pop(key, default=default)
        self._dirty = True

    def popitem(self):
        r = self.data.popitem()
        self._dirty = True
        return r

    def clear(self):
        self.data.clear()
        self._dirty = True

    def _clean_dirty(self):
        self._dirty = False

    def __getitem__(self, k):
        return self.data[k]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __delitem__(self, k):
        del self.data[k]
        self._dirty = True

    def __setitem__(self, k, v):
        self.data[k] = v
        self._dirty = True


class ProxyList(list):
    """
    Proxy for list, records when the list has been modified.
    """

    def __init__(self, iterable=None):
        list.__init__(self, iterable)
        self._dirty = False

    def _clean_dirty(self):
        self._dirty = False

    def append(self, item):
        list.append(self, item)
        self._dirty = True

    def clear(self):
        list.clear(self)
        self._dirty = True

    def extend(self, iterable):
        list.extend(self, iterable)
        self._dirty = True

    def insert(self, index, item):
        list.insert(self, index, item)
        self._dirty = True

    def remove(self, item):
        list.remove(self, item)
        self._dirty = True

    def pop(self, index=-1):
        r = list.pop(self, index)
        self._dirty = True
        return r

    def __delitem__(self, key):
        list.__delitem__(self, key)
        self._dirty = True

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self._dirty = True

    def __iadd__(self, other):
        r = list.__iadd__(self, other)
        self._dirty = True
        return r

    def __imul__(self, other):
        r = list.__imul__(self, other)
        self._dirty = True
        return r
