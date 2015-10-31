from zenpy.lib.objects.base_object import BaseObject


class ChangeEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._field_name = None
        self._previous_value = None
        self._type = None
        self.id = None
        self._value = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
