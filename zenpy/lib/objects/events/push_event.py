from zenpy.lib.objects.base_object import BaseObject


class PushEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.value_reference = None
        self.type = None
        self.id = None
        self.value = None

        for key, value in kwargs.items():
            setattr(self, key, value)
