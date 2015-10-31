from zenpy.lib.objects.base_object import BaseObject


class UserField(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.raw_title = None
        self.created_at = None
        self.description = None
        self.title = None
        self.url = None
        self.raw_description = None
        self.updated_at = None
        self.regexp_for_validation = None
        self.key = None
        self.active = None
        self.position = None
        self.type = None
        self.id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
