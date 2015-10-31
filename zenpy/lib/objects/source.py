from zenpy.lib.objects.base_object import BaseObject


class Source(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._to = None
        self._from_ = None
        self.rel = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
