
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class SatisfactionRatingEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.assignee_id = None
        self._body = None
        self._score = None
        self._type = None
        self.id = None
        
    @property
    def assignee(self):
        if self.api and self.assignee_id:
            return self.api.get_user(self.assignee_id)
    @assignee.setter
    def assignee(self, assignee):
            if assignee:
                self.assignee_id = assignee.id
    
    