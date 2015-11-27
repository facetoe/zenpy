from zenpy.lib.objects.base_object import BaseObject


class ChangeEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.field_name = None
        self.previous_value = None
        self.type = None
        self.id = None
        self.value = None

        for key, value in kwargs.items():
            setattr(self, key, value)
