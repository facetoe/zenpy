from zenpy.lib.objects.base_object import BaseObject


class TicketSharingEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.agreement_id = None
        self.action = None
        self.type = None
        self.id = None
