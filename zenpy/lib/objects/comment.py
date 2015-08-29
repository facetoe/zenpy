import os
from multiprocessing.pool import ThreadPool
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
			for attachment in self._attachments:
				yield self.api.object_from_json('attachment', attachment)
		else:
			yield []

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

	def save_attachments(self, out_path, exlude_suffixs=list()):
		urls = []
		for attachment in self.attachments:
			if not any([attachment.file_name.endswith(suffix) for suffix in exlude_suffixs]):
				urls.append((attachment.content_url, os.path.join(out_path, attachment.file_name)))
		p = ThreadPool(10)
		p.map(self.save, urls)

	def save(self, target_tuple):
		self._save(target_tuple[0], target_tuple[1])

	def _save(self, url, out_path):
		r = self.api._get(url, stream=True)
		if r.status_code == 200:
			with open(out_path, 'wb') as f:
				for chunk in r:
					f.write(chunk)
