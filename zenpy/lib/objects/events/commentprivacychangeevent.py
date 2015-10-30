from zenpy.lib.objects.base_object import BaseObject


class CommentPrivacyChangeEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._comment = None
        self.comment_id = None
        self.type = None
        self.id = None
        self.public = None

    @property
    def comment(self):
        if self.api and self.comment_id:
            return self.api.get_comment(self.comment_id)

    @comment.setter
    def comment(self, value):
        self._comment = value
