import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class TicketEvent(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.id = None
		self.via = None
		self._updater = None
		self.updater_id = None
		self.child_events = None
		self.timestamp = None
		self.ticket_id = None
		self._system = None

	@property
	def system(self):
		if self.api and self._system:
			return self.api.object_manager.object_from_json('system', self._system)

	@property
	def updater(self):
		if self.api and self.updater_id:
			return self.api.get_user(self.updater_id)

	@updater.setter
	def updater(self, value):
		self._updater = value
