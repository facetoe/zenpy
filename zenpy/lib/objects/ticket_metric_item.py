
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class TicketMetricItem(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._calendar = None
        self._business = None
        
    
    