
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Attachment(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._thumbnails = None
        self._file_name = None
        self._content_url = None
        self._content_type = None
        self.id = None
        self._size = None
        
    
    