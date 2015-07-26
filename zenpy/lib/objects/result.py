
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Result(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.count = None
		self.facets = None
		self.prev_page = None
		self._results = None
		self.next_page = None


	@property
	def results(self):
		return self.api.result_generator(vars(self))

	def __iter__(self):
		if self.api:
			return self.results

			

