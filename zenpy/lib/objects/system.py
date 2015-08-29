import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class System(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.latitude = None
		self.client = None
		self.ip_address = None
		self.location = None
		self.longitude = None
