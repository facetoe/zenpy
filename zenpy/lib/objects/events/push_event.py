
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class PushEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._value_reference = None
        self._type = None
        self.id = None
        self._value = None
        
    
    