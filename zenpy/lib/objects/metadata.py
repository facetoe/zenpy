
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Metadata(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._system = None
        self._custom = None
        
    @property
    def system(self):
        if self.api and self._system:
            return self.api.get_system(self._system)
    @system.setter
    def system(self, system):
            if system:
                self._system = system
    @property
    def custom(self):
        if self.api and self._custom:
            return self.api.get_custom(self._custom)
    @custom.setter
    def custom(self, custom):
            if custom:
                self._custom = custom
    
    