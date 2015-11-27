from zenpy.lib.objects.base_object import BaseObject


class CreateEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.type = None
        self.field_name = None
        self.id = None
        self.value = None

        for key, value in kwargs.items():
            setattr(self, key, value)
