import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Thumbnail(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.file_name = None
		self.content_type = None
		self.id = None
		self.content_url = None
		self.size = None
