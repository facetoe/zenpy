from zenpy.lib.objects.base_object import BaseObject


class FacebookCommentEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self.attachments = None
        self.type = None
        self.public = None
        self.graph_object_id = None
        self.author_id = None
        self._data = None
        self.id = None
        self.trusted = None
        self.html_body = None

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
