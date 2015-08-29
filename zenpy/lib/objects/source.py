import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Source(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.to = None
		self._from = None
		self.rel = None