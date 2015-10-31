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
        self.domain_names = None
        self.details = None
        self.notes = None
        self.group_id = None
        self.external_id = None
        self.id = None
        self.shared_tickets = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def group(self):
        if self.api and self.group_id:
            return self.api.get_group(self.group_id)

    @group.setter
    def group(self, group):
        if group:
            self.group_id = group.id

    @property
    def external(self):
        if self.api and self.external_id:
            return self.api.get_external(self.external_id)

    @external.setter
    def external(self, external):
        if external:
            self.external_id = external.id
