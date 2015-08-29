import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class JobStatus(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.status = None
		self.url = None
		self._results = None
		self.progress = None
		self.message = None
		self.total = None
		self.id = None

	@property
	def results(self):
		if self.api and self._results:
			for status in self._results:
				yield self.api.object_from_json('status', status)

	@results.setter
	def results(self, value):
		self._results = value
