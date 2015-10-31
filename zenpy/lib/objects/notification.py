
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Notification(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.body = None
        self._via = None
        self.recipients = None
        self.type = None
        self.id = None
        self.subject = None
        
    @property
    def via(self):
        if self.api and self._via:
            return self.api.get_via(self._via)
    @via.setter
    def via(self, via):
            self._via = via
    
    