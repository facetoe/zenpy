
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class ExternalEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._body = None
        self._resource = None
        self._type = None
        self.id = None
        
    
    