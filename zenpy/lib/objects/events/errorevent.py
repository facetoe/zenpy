from zenpy.lib.objects.base_object import BaseObject


class ErrorEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.message = None
        self.type = None
        self.id = None
