from zenpy.lib.objects.base_object import BaseObject


class ExternalEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.body = None
        self.resource = None
        self.type = None
        self.id = None
