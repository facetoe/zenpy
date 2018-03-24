class ProxyDict(dict):
    """
    Proxy for dict, records when the dictionary has been modified.
    """

    def __init__(self, *args, **kwargs):
        self.dirty_callback = kwargs.pop('dirty_callback', None)
        super(dict, self).__init__()
        dict.update(self, *args, **kwargs)
        self._set_dirty()

    def update(self, *args, **kwargs):
        dict.update(self, *args, **kwargs)
        self._set_dirty()

    def pop(self, key, default=None):
        dict.pop(self, key, default=default)
        self._set_dirty()

    def popitem(self):
        r = dict.popitem(self)
        self._set_dirty()
        return r

    def clear(self):
        dict.clear(self)
        self._set_dirty()

    def _clean_dirty(self):
        self._dirty = False

    def _set_dirty(self):
        if self.dirty_callback is not None:
            self.dirty_callback()
        self._dirty = True

    def __getitem__(self, k):
        def dirty_callback():
            self._set_dirty()

        element = dict.__getitem__(self, k)
        if isinstance(element, list):
            element = ProxyList(element, dirty_callback=dirty_callback)
            dict.__setitem__(self, k, element)
        elif isinstance(element, dict):
            element = ProxyDict(element, dirty_callback=dirty_callback)
            dict.__setitem__(self, k, element)
        elif getattr(element, '_dirty_callback', None) is not None:
            element._dirty_callback = dirty_callback
        return self[k]

    def __delitem__(self, k):
        dict.__delitem__(self, k)
        self._set_dirty()

    def __setitem__(self, k, v):
        dict.__setitem__(self, k, v)
        self._set_dirty()


class ProxyList(list):
    """
    Proxy for list, records when the list has been modified.
    """

    def __init__(self, iterable=None, dirty_callback=None):
        list.__init__(self, iterable)
        self.dirty_callback = dirty_callback
        self._dirty = False

    def _clean_dirty(self):
        self._dirty = False

    def _set_dirty(self):
        if self.dirty_callback is not None:
            self.dirty_callback()
        self._dirty = True

    def append(self, item):
        list.append(self, item)
        self._set_dirty()

    def clear(self):
        list.clear(self)
        self._set_dirty()

    def extend(self, iterable):
        list.extend(self, iterable)
        self._set_dirty()

    def insert(self, index, item):
        list.insert(self, index, item)
        self._set_dirty()

    def remove(self, item):
        list.remove(self, item)
        self._set_dirty()

    def __getitem__(self, item):
        def dirty_callback():
            self._set_dirty()

        element = list.__getitem__(self, item)
        if isinstance(element, list):
            element = ProxyList(element, dirty_callback=dirty_callback)
            self[item] = element
        elif isinstance(element, dict):
            element = ProxyDict(element, dirty_callback=dirty_callback)
            self[item] = element
        elif getattr(element, '_dirty_callback', None) is not None:
            element._dirty_callback = dirty_callback
        return element

    def pop(self, index=-1):
        r = list.pop(self, index)
        self._set_dirty()
        return r

    def __delitem__(self, key):
        list.__delitem__(self, key)
        self._set_dirty()

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self._set_dirty()

    def __iadd__(self, other):
        r = list.__iadd__(self, other)
        self._set_dirty()
        return r

    def __imul__(self, other):
        r = list.__imul__(self, other)
        self._set_dirty()
        return r
