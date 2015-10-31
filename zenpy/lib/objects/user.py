
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class User(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._locale = None
        self._photo = None
        self.updated_at = None
        self.locale_id = None
        self.moderator = None
        self.custom_role_id = None
        self.suspended = None
        self.id = None
        self._user_fields = None
        self.verified = None
        self._role = None
        self._details = None
        self.shared = None
        self._email = None
        self.chat_only = None
        self.tags = None
        self.restricted_agent = None
        self.organization_id = None
        self._phone = None
        self.last_login_at = None
        self.active = None
        self._two_factor_auth_enabled = None
        self.shared_agent = None
        self._ticket_restriction = None
        self._name = None
        self.only_private_comments = None
        self._url = None
        self.created_at = None
        self._time_zone = None
        self._alias = None
        self._signature = None
        self.external_id = None
        self._notes = None
        
    @property
    def photo(self):
        if self.api and self._photo:
            return self.api.get_photo(self._photo)
    @photo.setter
    def photo(self, photo):
            if photo:
                self._photo = photo
    @property
    def custom_role(self):
        if self.api and self.custom_role_id:
            return self.api.get_custom_role(self.custom_role_id)
    @custom_role.setter
    def custom_role(self, custom_role):
            if custom_role:
                self.custom_role_id = custom_role.id
    @property
    def user_fields(self):
        if self.api and self._user_fields:
            return self.api.get_user_fields(self._user_fields)
    @user_fields.setter
    def user_fields(self, user_fields):
            if user_fields:
                self._user_fields = user_fields
    @property
    def details(self):
        if self.api and self._details:
            return self.api.get_details(self._details)
    @details.setter
    def details(self, details):
            if details:
                self._details = details
    @property
    def organization(self):
        if self.api and self.organization_id:
            return self.api.get_organization(self.organization_id)
    @organization.setter
    def organization(self, organization):
            if organization:
                self.organization_id = organization.id
    @property
    def phone(self):
        if self.api and self._phone:
            return self.api.get_phone(self._phone)
    @phone.setter
    def phone(self, phone):
            if phone:
                self._phone = phone
    @property
    def two_factor_auth_enabled(self):
        if self.api and self._two_factor_auth_enabled:
            return self.api.get_two_factor_auth_enabled(self._two_factor_auth_enabled)
    @two_factor_auth_enabled.setter
    def two_factor_auth_enabled(self, two_factor_auth_enabled):
            if two_factor_auth_enabled:
                self._two_factor_auth_enabled = two_factor_auth_enabled
    @property
    def alias(self):
        if self.api and self._alias:
            return self.api.get_alias(self._alias)
    @alias.setter
    def alias(self, alias):
            if alias:
                self._alias = alias
    @property
    def signature(self):
        if self.api and self._signature:
            return self.api.get_signature(self._signature)
    @signature.setter
    def signature(self, signature):
            if signature:
                self._signature = signature
    @property
    def external(self):
        if self.api and self.external_id:
            return self.api.get_external(self.external_id)
    @external.setter
    def external(self, external):
            if external:
                self.external_id = external.id
    @property
    def notes(self):
        if self.api and self._notes:
            return self.api.get_notes(self._notes)
    @notes.setter
    def notes(self, notes):
            if notes:
                self._notes = notes
    
    