
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class OrganizationActivityEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._body = None
        self._via = None
        self._recipients = None
        self._type = None
        self.id = None
        self._subject = None
        
    @property
    def via(self):
        if self.api and self._via:
            return self.api.get_via(self._via)
    @via.setter
    def via(self, via):
            if via:
                self._via = via
    
    