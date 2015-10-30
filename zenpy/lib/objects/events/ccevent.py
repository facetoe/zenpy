from zenpy.lib.objects.base_object import BaseObject


class CcEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.via = None
        self.type = None
        self.id = None
        self.recipients = None
