
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Brand(BaseObject):
	def __init__(self, api=None):
		self.api = api
		self.default = None
		self.name = None
		self.url = None
		self.created_at = None
		self.updated_at = None
		self.active = None
		self.brand_url = None
		self.logo = None
		self.help_center_state = None
		self.has_help_center = None
		self.subdomain = None
		self.id = None
		self.host_mapping = None



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
		
