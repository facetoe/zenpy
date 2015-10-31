
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Status(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._status = None
        self._errors = None
        self.success = None
        self._title = None
        self._action = None
        self.id = None
        
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    
    