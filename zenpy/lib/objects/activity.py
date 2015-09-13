import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Activity(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.title = None
		self.url = None
		self._created = None
		self.created_at = None
		self._updated = None
		self.updated_at = None
		self._actor = None
		self.verb = None
		self._user = None
		self.id = None

	@property
	def user(self):
		if self._user:
			return self.api.object_manager.object_from_json('user', self._user)

	@user.setter
	def user(self, value):
		self._user = value

	@property
	def actor(self):
		if self._actor:
			return self.api.object_manager.object_from_json('user', self._actor)

	@actor.setter
	def actor(self, value):
		self._actor = value

	@property
	def created(self):
		if self.created_at:
			return dateutil.parser.parse(self.created_at)

	@created.setter
	def created(self, value):
		self._created = value

	@property
	def updated(self):
		if self.updated_at:
			return dateutil.parser.parse(self.updated_at)

	@updated.setter
	def updated(self, value):
		self._updated = value
