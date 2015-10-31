from zenpy.lib.objects.base_object import BaseObject


class System(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.latitude = None
        self.client = None
        self.ip_address = None
        self.location = None
        self.longitude = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
