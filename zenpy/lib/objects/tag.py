
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Tag(BaseObject):
	def __init__(self, api=None, name=None):
		self.api = api
		self.count = None
		self.name = name



