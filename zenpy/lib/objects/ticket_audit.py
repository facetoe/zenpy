from zenpy.lib.objects.base_object import BaseObject


class TicketAudit(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._audit = None
        self._ticket = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
