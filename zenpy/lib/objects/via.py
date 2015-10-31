
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Via(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._source = None
        
    @property
    def source(self):
        if self.api and self._source:
            return self.api.get_source(self._source)
    @source.setter
    def source(self, source):
            if source:
                self._source = source
    
    