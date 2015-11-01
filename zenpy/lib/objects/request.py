import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Request(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.status = None
        self.organization_id = None
        self._via = None
        self.description = None
        self.url = None
        self._fields = None
        self.created_at = None
        self.can_be_solved_by_me = None
        self.updated_at = None
        self.collaborator_ids = None
        self.priority = None
        self.due_at = None
        self.assignee_id = None
        self.requester_id = None
        self.type = None
        self.id = None
        self._custom_fields = None
        self.subject = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def organization(self):
        if self.api and self.organization_id:
            return self.api.get_organization(self.organization_id)

    @organization.setter
    def organization(self, organization):
        if organization:
            self.organization_id = organization.id

    @property
    def via(self):
        if self.api and self._via:
            return self.api.get_via(self._via)

    @via.setter
    def via(self, via):
        if via:
            self._via = via

    @property
    def fields(self):
        if self.api and self._fields:
            return self.api.get_fields(self._fields)

    @fields.setter
    def fields(self, fields):
        if fields:
            self._fields = fields

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
    def collaborators(self):
        if self.api and self.collaborator_ids:
            return self.api.get_users(self.collaborator_ids)

    @collaborators.setter
    def collaborators(self, collaborators):
        if collaborators:
            self.collaborator_ids = [o.id for o in collaborators]

    @property
    def due(self):
        if self.due_at:
            return dateutil.parser.parse(self.due_at)

    @due.setter
    def due(self, due):
        if due:
            self.due_at = due_at

    @property
    def assignee(self):
        if self.api and self.assignee_id:
            return self.api.get_user(self.assignee_id)

    @assignee.setter
    def assignee(self, assignee):
        if assignee:
            self.assignee_id = assignee.id

    @property
    def requester(self):
        if self.api and self.requester_id:
            return self.api.get_user(self.requester_id)

    @requester.setter
    def requester(self, requester):
        if requester:
            self.requester_id = requester.id

    @property
    def custom_fields(self):
        if self.api and self._custom_fields:
            return self.api.get_custom_fields(self._custom_fields)

    @custom_fields.setter
    def custom_fields(self, custom_fields):
        if custom_fields:
            self._custom_fields = custom_fields
