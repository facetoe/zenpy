from zenpy.lib.objects.base_object import BaseObject


class Tag(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.count = None
        self.name = None

        for key, value in kwargs.items():
            setattr(self, key, value)
