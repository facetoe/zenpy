import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class TicketMetric(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self._solved = None
		self.solved_at = None
		self._updated = None
		self.updated_at = None
		self._assigned = None
		self.assigned_at = None
		self.reopens = None
		self.replies = None
		self.first_resolution_time_in_minutes = None
		self.on_hold_time_in_minutes = None
		self._created = None
		self.created_at = None
		self._ticket = None
		self.ticket_id = None
		self._assignee_updated = None
		self.assignee_updated_at = None
		self.group_stations = None
		self.assignee_stations = None
		self._status_updated = None
		self.status_updated_at = None
		self.reply_time_in_minutes = None
		self._requester_updated = None
		self.requester_updated_at = None
		self._latest_comment_added = None
		self.latest_comment_added_at = None
		self._initially_assigned = None
		self.initially_assigned_at = None
		self.id = None
		self.full_resolution_time_in_minutes = None
		self.requester_wait_time_in_minutes = None
		self.agent_wait_time_in_minutes = None

	@property
	def solved(self):
		if self.solved_at:
			return dateutil.parser.parse(self.solved_at)

	@solved.setter
	def solved(self, value):
		self._solved = value

	@property
	def updated(self):
		if self.updated_at:
			return dateutil.parser.parse(self.updated_at)

	@updated.setter
	def updated(self, value):
		self._updated = value

	@property
	def assigned(self):
		if self.assigned_at:
			return dateutil.parser.parse(self.assigned_at)

	@assigned.setter
	def assigned(self, value):
		self._assigned = value

	@property
	def created(self):
		if self.created_at:
			return dateutil.parser.parse(self.created_at)

	@created.setter
	def created(self, value):
		self._created = value

	@property
	def ticket(self):
		if self.api and self.ticket_id:
			return self.api.get_ticket(self.ticket_id)

	@ticket.setter
	def ticket(self, value):
		self._ticket = value

	@property
	def assignee_updated(self):
		if self.assignee_updated_at:
			return dateutil.parser.parse(self.assignee_updated_at)

	@assignee_updated.setter
	def assignee_updated(self, value):
		self._assignee_updated = value

	@property
	def status_updated(self):
		if self.status_updated_at:
			return dateutil.parser.parse(self.status_updated_at)

	@status_updated.setter
	def status_updated(self, value):
		self._status_updated = value

	@property
	def requester_updated(self):
		if self.requester_updated_at:
			return dateutil.parser.parse(self.requester_updated_at)

	@requester_updated.setter
	def requester_updated(self, value):
		self._requester_updated = value

	@property
	def latest_comment_added(self):
		if self.latest_comment_added_at:
			return dateutil.parser.parse(self.latest_comment_added_at)

	@latest_comment_added.setter
	def latest_comment_added(self, value):
		self._latest_comment_added = value

	@property
	def initially_assigned(self):
		if self.initially_assigned_at:
			return dateutil.parser.parse(self.initially_assigned_at)

	@initially_assigned.setter
	def initially_assigned(self, value):
		self._initially_assigned = value
