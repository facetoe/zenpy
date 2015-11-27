from zenpy.lib.objects.base_object import BaseObject


class VoiceCommentEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self.formatted_to = None
        self.formatted_from = None
        self.type = None
        self.public = None
        self._attachments = None
        self.transcription_visible = None
        self.author_id = None
        self._data = None
        self.id = None
        self.trusted = None
        self.html_body = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def attachments(self):
        if self.api and self._attachments:
            return self.api.get_attachments(self._attachments)

    @attachments.setter
    def attachments(self, attachments):
        if attachments:
            self._attachments = attachments

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
