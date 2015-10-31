from zenpy.lib.objects.base_object import BaseObject


class FacebookEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self.communication = None
        self.ticket_via = None
        self.type = None
        self.id = None
        self._page = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
