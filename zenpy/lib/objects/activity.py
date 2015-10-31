from zenpy.lib.objects.base_object import BaseObject


class Activity(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.title = None
        self.url = None
        self.created_at = None
        self.updated_at = None
        self.actor = None
        self.verb = None
        self.user = None
        self.id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
