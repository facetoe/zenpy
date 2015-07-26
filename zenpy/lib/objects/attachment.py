from zenpy.lib.objects.base_object import BaseObject


class Attachment(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self._thumbnails = None
		self.file_name = None
		self.content_url = None
		self.content_type = None
		self.id = None
		self.size = None

	@property
	def thumbnails(self):
		if self.api and self._thumbnails:
			return self.api.get_thumbnails(self._thumbnails)
		else:
			return []

	@thumbnails.setter
	def thumbnails(self, value):
		self._thumbnails = value
