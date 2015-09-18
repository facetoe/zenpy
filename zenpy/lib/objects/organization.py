
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Organization(BaseObject):
	def __init__(self, api=None, name=None, tags=None):
		self.api = api
		self.name = name
		self.tags = tags
		self.shared_comments = None
		self.url = None
		self.organization_fields = None
		self.created_at = None
		self.updated_at = None
		self.domain_names = None
		self.details = None
		self.notes = None
		self._group = None
		self.group_id = None
		self._external = None
		self.external_id = None
		self.id = None
		self.shared_tickets = None



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
	def group(self):
		if self.api and self.group_id:
			return self.api.get_group(self.group_id)

	@group.setter
	def group(self, value):
		self._group = value
		
	@property
	def external(self):
		if self.api and self.external_id:
			return self.api.get_external(self.external_id)

	@external.setter
	def external(self, value):
		self._external = value
		
