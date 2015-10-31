
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Source(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._to = None
        self._from_ = None
        self._rel = None
        
    @property
    def to(self):
        if self.api and self._to:
            return self.api.get_to(self._to)
    @to.setter
    def to(self, to):
            if to:
                self._to = to
    @property
    def from_(self):
        if self.api and self._from_:
            return self.api.get_from_(self._from_)
    @from_.setter
    def from_(self, from_):
            if from_:
                self._from_ = from_
    
    