from zenpy.lib.objects.base_object import BaseObject


class Metadata(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._system = None
        self._custom = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
