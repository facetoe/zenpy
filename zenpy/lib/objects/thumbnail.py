
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Thumbnail(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._file_name = None
        self._content_type = None
        self.id = None
        self._content_url = None
        self._size = None
        
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    
    