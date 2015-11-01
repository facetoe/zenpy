import dateutil.parser

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

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated
