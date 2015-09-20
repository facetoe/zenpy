
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class User(BaseObject):
	def __init__(self, api=None, **kwargs):
		self.api = api
		self.locale = None
		self._photo = None
		self.updated_at = None
		self._locale = None
		self.locale_id = None
		self.moderator = None
		self._custom_role = None
		self.custom_role_id = None
		self.suspended = None
		self.id = None
		self.user_fields = None
		self.verified = None
		self.role = None
		self.details = None
		self.shared = None
		self.email = None
		self.chat_only = None
		self.tags = None
		self.restricted_agent = None
		self._organization = None
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
		self._external = None
		self.external_id = None
		self.notes = None

		for key, value in kwargs.iteritems():
			setattr(self, key, value)

	@property
	def updated(self):
		if self.updated_at:
			return dateutil.parser.parse(self.updated_at)
			

	@updated.setter
	def updated(self, value):
		self._updated = value
		
	@property
	def custom_role(self):
		if self.api and self.custom_role_id:
			return self.api.get_custom_role(self.custom_role_id)

	@custom_role.setter
	def custom_role(self, value):
		self._custom_role = value
		
	@property
	def organization(self):
		if self.api and self.organization_id:
			return self.api.get_organization(self.organization_id)

	@organization.setter
	def organization(self, value):
		self._organization = value
		
	@property
	def last_login(self):
		if self.last_login_at:
			return dateutil.parser.parse(self.last_login_at)
			

	@last_login.setter
	def last_login(self, value):
		self._last_login = value
		
	@property
	def created(self):
		if self.created_at:
			return dateutil.parser.parse(self.created_at)
			

	@created.setter
	def created(self, value):
		self._created = value
		
	@property
	def external(self):
		if self.api and self.external_id:
			return self.api.get_external(self.external_id)

	@external.setter
	def external(self, value):
		self._external = value

	@property
	def photo(self):
		if self.api and self._photo:
			return self.api.object_manager.object_from_json('photo', self._photo)
		
