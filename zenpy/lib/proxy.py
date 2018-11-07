class ProxyDict(dict):
    """
    Proxy for dict, records when the dictionary has been modified.
    """

    def __init__(self, *args, **kwargs):
        self.dirty_callback = kwargs.pop('dirty_callback', None)
        super(dict, self).__init__()
        dict.update(self, *args, **kwargs)
        self._sentinel = object()
        self._dirty = False

    def update(self, *args, **kwargs):
        dict.update(self, *args, **kwargs)
        self._set_dirty()

    def pop(self, key, default=None):
        dict.pop(self, key, default)
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
        element = dict.__getitem__(self, k)
        wrapped = self._wrap_element(element)
        dict.__setitem__(self, k, wrapped)
        return wrapped

    def __delitem__(self, k):
        dict.__delitem__(self, k)
        self._set_dirty()

    def __setitem__(self, k, v):
        dict.__setitem__(self, k, v)
        self._set_dirty()

    def _wrap_element(self, element):
        """
        We want to know if an item is modified that is stored in this dict. If the element is a list or dict,
        we wrap it in a ProxyList or ProxyDict, and if it is modified execute a callback that updates this
        instance. If it is a ZenpyObject, then the callback updates the parent object.
        """

        def dirty_callback():
            self._set_dirty()

        if isinstance(element, list):
            element = ProxyList(element, dirty_callback=dirty_callback)
        elif isinstance(element, dict):
            element = ProxyDict(element, dirty_callback=dirty_callback)
        # If it is a Zenpy object this will either return None or the previous wrapper.
        elif getattr(element, '_dirty_callback', self._sentinel) is not self._sentinel:
            # Don't set callback if already set.
            if not callable(element._dirty_callback):
                element._dirty_callback = dirty_callback
        return element


class ProxyList(list):
    """
    Proxy for list, records when the list has been modified.
    """

    def __init__(self, iterable=None, dirty_callback=None):
        list.__init__(self, iterable or [])
        self.dirty_callback = dirty_callback
        self._dirty = False
        self._sentinel = object()

        # Doesn't exist in 2.7
        if hasattr(list, 'clear'):
            def clear():
                list.clear(self)
                self._set_dirty()
            self.clear = clear

    def _clean_dirty(self):
        self._dirty = False

    def _set_dirty(self):
        if self.dirty_callback is not None:
            self.dirty_callback()
        self._dirty = True

    def append(self, item):
        list.append(self, item)
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
        element = list.__getitem__(self, item)
        wrapped = self._wrap_element(element)
        self[item] = wrapped
        return wrapped

    def __iter__(self):
        for index, element in enumerate(list.__iter__(self), start=0):
            wrapped = self._wrap_element(element)
            self[index] = wrapped
            yield wrapped

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

    def _wrap_element(self, element):
        """
        We want to know if an item is modified that is stored in this list. If the element is a list or dict,
        we wrap it in a ProxyList or ProxyDict, and if it is modified execute a callback that updates this
        instance. If it is a ZenpyObject, then the callback updates the parent object.
        """

        def dirty_callback():
            self._set_dirty()

        if isinstance(element, list):
            element = ProxyList(element, dirty_callback=dirty_callback)
        elif isinstance(element, dict):
            element = ProxyDict(element, dirty_callback=dirty_callback)
        # If it is a Zenpy object this will either return None or the previous wrapper.
        elif getattr(element, '_dirty_callback', self._sentinel) is not self._sentinel:
            # Don't set callback if already set.
            if not callable(element._dirty_callback):
                element._dirty_callback = dirty_callback
        return element
