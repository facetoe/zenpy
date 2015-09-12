import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Via(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self._source = None
		self.channel = None

	@property
	def source(self):
		if self.api and self._source:
			return self.api.object_manager.object_from_json('source', self._source)

	@source.setter
	def source(self, value):
		self._source = value
