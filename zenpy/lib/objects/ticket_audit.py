import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class TicketAudit(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.audit = None
		self.ticket = None
