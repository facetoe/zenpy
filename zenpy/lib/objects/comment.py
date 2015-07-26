import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Comment(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.body = None
		self.via = None
		self.attachments = None
		self._attachments = None
		self.created_at = None
		self.public = None
		self._author = None
		self.author_id = None
		self.type = None
		self.id = None
		self.metadata = None

	@property
	def attachments(self):
		if self.api and self._attachments:
			return self.api.get_attachments(self._attachments)
		else:
			return []

	@attachments.setter
	def attachments(self, value):
		self._attachments = value

	@property
	def created(self):
		if self.created_at:
			return dateutil.parser.parse(self.created_at)


	@created.setter
	def created(self, value):
		self._created = value

	@property
	def author(self):
		if self.api and self.author_id:
			return self.api.get_author(self.author_id)

	@author.setter
	def author(self, value):
		self._author = value
