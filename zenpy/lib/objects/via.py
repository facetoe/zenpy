from zenpy.lib.objects.base_object import BaseObject


class Via(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._source = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
