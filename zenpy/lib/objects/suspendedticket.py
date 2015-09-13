import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class SuspendedTicket(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.via = None
		self.author = None
		self.url = None
		self.recipient = None
		self.created_at = None
		self._created = None
		self.updated_at = None
		self._updated = None
		self.content = None
		self._brand = None
		self.brand_id = None
		self._ticket = None
		self.ticket_id = None
		self.cause = None
		self.id = None
		self.subject = None

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

	@property
	def brand(self):
		if self.api and self.brand_id:
			return self.api.get_brand(self.brand_id)

	@brand.setter
	def brand(self, value):
		self._brand = value

	@property
	def ticket(self):
		if self.api and self.ticket_id:
			return self.api.get_ticket(self.ticket_id)

	@ticket.setter
	def ticket(self, value):
		self._ticket = value
