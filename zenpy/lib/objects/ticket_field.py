
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class TicketField(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.raw_title = None
        self.created_at = None
        self.description = None
        self.title = None
        self.url = None
        self.visible_in_portal = None
        self.raw_description = None
        self.required = None
        self.updated_at = None
        self.required_in_portal = None
        self.collapsed_for_agents = None
        self.regexp_for_validation = None
        self.tag = None
        self.raw_title_in_portal = None
        self.title_in_portal = None
        self.active = None
        self.position = None
        self.type = None
        self.id = None
        self.editable_in_portal = None
        
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)
    @created.setter
    def created(self, created):
            if created:
                self.created_at = created
    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)
    @updated.setter
    def updated(self, updated):
            if updated:
                self.updated_at = updated
    
    