
import dateutil.parser
from zenpy.lib.objects.base_object import BaseObject

class VoiceCommentEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._body = None
        self._formatted_to = None
        self._formatted_from = None
        self._type = None
        self.public = None
        self._attachments = None
        self.transcription_visible = None
        self.author_id = None
        self._data = None
        self.id = None
        self.trusted = None
        self._html_body = None
        
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def author(self):
        if self.api and self.author_id:
            return self.api.get_user(self.author_id)
    @author.setter
    def author(self, author):
            if author:
                self.author_id = author.id
    @property
    def data(self):
        if self.api and self._data:
            return self.api.get_data(self._data)
    @data.setter
    def data(self, data):
            if data:
                self._data = data
    
    