import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject


class FacebookCommentEvent(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.body = None
		self.attachments = None
		self.type = None
		self.public = None
		self._graph_object = None
		self._graph_object = None
		self.graph_object_id = None
		self._author = None
		self.author_id = None
		self.data = None
		self.id = None
		self.trusted = None
		self.html_body = None

	@property
	def author(self):
		if self.api and self.author_id:
			return self.api.get_user(self.author_id)

	@author.setter
	def author(self, value):
		self._author = value
