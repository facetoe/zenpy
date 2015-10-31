
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Request(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._status = None
        self.organization_id = None
        self._via = None
        self._description = None
        self._url = None
        self._fields = None
        self.created_at = None
        self.can_be_solved_by_me = None
        self.updated_at = None
        self.collaborator_ids = None
        self._priority = None
        self.due_at = None
        self.assignee_id = None
        self.requester_id = None
        self._type = None
        self.id = None
        self._custom_fields = None
        self._subject = None
        
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
    def priority(self):
        if self.api and self._priority:
            return self.api.get_priority(self._priority)
    @priority.setter
    def priority(self, priority):
            if priority:
                self._priority = priority
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
    def type(self):
        if self.api and self._type:
            return self.api.get_type(self._type)
    @type.setter
    def type(self, type):
            if type:
                self._type = type
    
    