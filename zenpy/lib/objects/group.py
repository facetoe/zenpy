import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Group(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.name = None
        self.url = None
        self.created_at = None
        self.updated_at = None
        self.deleted = None
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
            self.created_at = created_at

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated_at
