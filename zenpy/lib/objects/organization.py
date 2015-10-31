
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Organization(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._name = None
        self.shared_comments = None
        self._url = None
        self._organization_fields = None
        self.created_at = None
        self.tags = None
        self.updated_at = None
        self._domain_names = None
        self._details = None
        self._notes = None
        self.group_id = None
        self.external_id = None
        self.id = None
        self.shared_tickets = None
        
    @property
    def organization_fields(self):
        if self.api and self._organization_fields:
            return self.api.get_organization_fields(self._organization_fields)
    @organization_fields.setter
    def organization_fields(self, organization_fields):
            if organization_fields:
                self._organization_fields = organization_fields
    @property
    def details(self):
        if self.api and self._details:
            return self.api.get_details(self._details)
    @details.setter
    def details(self, details):
            if details:
                self._details = details
    @property
    def notes(self):
        if self.api and self._notes:
            return self.api.get_notes(self._notes)
    @notes.setter
    def notes(self, notes):
            if notes:
                self._notes = notes
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
    
    