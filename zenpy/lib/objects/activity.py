
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class Activity(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._title = None
        self._url = None
        self.created_at = None
        self.updated_at = None
        self._actor = None
        self._verb = None
        self._user = None
        self.id = None
        
    @property
    def actor(self):
        if self.api and self._actor:
            return self.api.get_actor(self._actor)
    @actor.setter
    def actor(self, actor):
            if actor:
                self._actor = actor
    @property
    def user(self):
        if self.api and self._user:
            return self.api.get_user(self._user)
    @user.setter
    def user(self, user):
            if user:
                self._user = user
    
    