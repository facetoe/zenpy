import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Attachment(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.thumbnails = None
		self.file_name = None
		self.content_url = None
		self.content_type = None
		self.id = None
		self.size = None
