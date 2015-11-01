import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Organization(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.name = None
        self.shared_comments = None
        self.url = None
        self._organization_fields = None
        self.created_at = None
        self.tags = None
        self.updated_at = None
        self._domain_names = None
        self.details = None
        self.notes = None
        self.group_id = None
        self.external_id = None
        self.id = None
        self.shared_tickets = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def organization_fields(self):
        if self.api and self._organization_fields:
            return self.api.get_organization_fields(self._organization_fields)

    @organization_fields.setter
    def organization_fields(self, organization_fields):
        if organization_fields:
            self._organization_fields = organization_fields

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

    @property
    def group(self):
        if self.api and self.group_id:
            return self.api.get_group(self.group_id)

    @group.setter
    def group(self, group):
        if group:
            self.group_id = group.id
