from zenpy.lib.objects.base_object import BaseObject


class Request(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.status = None
        self.organization_id = None
        self._via = None
        self.description = None
        self.url = None
        self.fields = None
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
        self.custom_fields = None
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
    def collaborators(self):
        if self.api and self.collaborator_ids:
            return self.api.get_users(self.collaborator_ids)

    @collaborators.setter
    def collaborators(self, collaborators):
        if collaborators:
            self.collaborator_ids = [o.id for o in collaborators]

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
