
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Tag(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._count = None
        self._name = None
        
    
    