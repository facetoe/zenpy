import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Request(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.status = None
        self._organization = None
        self.organization_id = None
        self.via = None
        self.description = None
        self.url = None
        self.fields = None
        self._created = None
        self.created_at = None
        self.can_be_solved_by_me = None
        self._updated = None
        self.updated_at = None
        self.collaborator_ids = None
        self.priority = None
        self._due = None
        self.due_at = None
        self._assignee = None
        self.assignee_id = None
        self._requester = None
        self.requester_id = None
        self.type = None
        self.id = None
        self.custom_fields = None
        self.subject = None

    @property
    def organization(self):
        if self.api and self.organization_id:
            return self.api.get_organization(self.organization_id)

    @organization.setter
    def organization(self, organization):
        self.organization_id = organization.id

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @property
    def due(self):
        if self.due_at:
            return dateutil.parser.parse(self.due_at)

    @property
    def assignee(self):
        if self.api and self.assignee_id:
            return self.api.get_user(self.assignee_id)

    @assignee.setter
    def assignee(self, user):
        self.assignee_id = user.id

    @property
    def requester(self):
        if self.api and self.requester_id:
            return self.api.get_user(self.requester_id)

    @requester.setter
    def requester(self, user):
        self.requester_id = user.id
