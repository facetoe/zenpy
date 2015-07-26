
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Forum(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.access = None
		self.locked = None
		self.name = None
		self.tags = None
		self.url = None
		self.created_at = None
		self.forum_type = None
		self.updated_at = None
		self._locale = None
		self.locale_id = None
		self._organization = None
		self.organization_id = None
		self.position = None
		self._category = None
		self.category_id = None
		self.description = None
		self.id = None



	@property
	def created(self):
		if self.created_at:
			return dateutil.parser.parse(self.created_at)
			

	@created.setter
	def created(self, value):
		self._created = value
		
	@property
	def updated(self):
		if self.updated_at:
			return dateutil.parser.parse(self.updated_at)
			

	@updated.setter
	def updated(self, value):
		self._updated = value
		
	@property
	def organization(self):
		if self.api and self.organization_id:
			return self.api.get_organization(self.organization_id)

	@organization.setter
	def organization(self, value):
		self._organization = value
		
	@property
	def category(self):
		if self.api and self.category_id:
			return self.api.get_category(self.category_id)

	@category.setter
	def category(self, value):
		self._category = value
		
