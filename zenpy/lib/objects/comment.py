from zenpy.lib.objects.base_object import BaseObject


class Comment(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self._via = None
        self.attachments = None
        self.created_at = None
        self.public = None
        self.author_id = None
        self.type = None
        self.id = None
        self._metadata = None

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
