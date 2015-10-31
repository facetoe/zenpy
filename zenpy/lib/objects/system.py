
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class System(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._latitude = None
        self._client = None
        self._ip_address = None
        self._location = None
        self._longitude = None
        
    @property
    def latitude(self):
        if self.api and self._latitude:
            return self.api.get_latitude(self._latitude)
    @latitude.setter
    def latitude(self, latitude):
            if latitude:
                self._latitude = latitude
    @property
    def longitude(self):
        if self.api and self._longitude:
            return self.api.get_longitude(self._longitude)
    @longitude.setter
    def longitude(self, longitude):
            if longitude:
                self._longitude = longitude
    
    