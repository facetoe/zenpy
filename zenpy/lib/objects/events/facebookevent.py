from zenpy.lib.objects.base_object import BaseObject


class FacebookEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.body = None
        self.communication = None
        self.ticket_via = None
        self.type = None
        self.id = None
        self.page = None
