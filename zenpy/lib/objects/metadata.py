import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Metadata(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self._system = None
		self.custom = None

	@property
	def system(self):
		if self.api and self._system:
			return self.api.object_from_json('system', self._system)

	@system.setter
	def system(self, value):
		self._system = value
