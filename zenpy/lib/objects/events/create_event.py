
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class CreateEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._type = None
        self._field_name = None
        self.id = None
        self._value = None
        
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    
    