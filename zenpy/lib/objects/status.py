import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Status(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.status = None
		self.errors = None
		self.success = None
		self.title = None
		self.action = None
		self.id = None
