from zenpy.lib.objects.base_object import BaseObject


class CcEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._via = None
        self.type = None
        self.id = None
        self.recipients = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
