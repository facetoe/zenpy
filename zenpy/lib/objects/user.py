import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class User(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.locale = None
        self.photo = None
        self.updated_at = None
        self.locale_id = None
        self.moderator = None
        self.custom_role_id = None
        self.suspended = None
        self.id = None
        self._user_fields = None
        self.verified = None
        self.role = None
        self.details = None
        self.shared = None
        self.email = None
        self.chat_only = None
        self.tags = None
        self.restricted_agent = None
        self.organization_id = None
        self.phone = None
        self.last_login_at = None
        self.active = None
        self.two_factor_auth_enabled = None
        self.shared_agent = None
        self.ticket_restriction = None
        self.name = None
        self.only_private_comments = None
        self.url = None
        self.created_at = None
        self.time_zone = None
        self.alias = None
        self.signature = None
        self.external_id = None
        self.notes = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated

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
    def organization(self):
        if self.api and self.organization_id:
            return self.api.get_organization(self.organization_id)

    @organization.setter
    def organization(self, organization):
        if organization:
            self.organization_id = organization.id

    @property
    def last_login(self):
        if self.last_login_at:
            return dateutil.parser.parse(self.last_login_at)

    @last_login.setter
    def last_login(self, last_login):
        if last_login:
            self.last_login_at = last_login

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created
