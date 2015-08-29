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
			for thumbnail in self._thumbnails:
				yield self.api.object_from_json('thumbnail', thumbnail)

	@thumbnails.setter
	def thumbnails(self, value):
		self._thumbnails = value
