from zenpy.lib.objects.base_object import BaseObject


class CommentPrivacyChangeEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.comment_id = None
        self.type = None
        self.id = None
        self.public = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def comment(self):
        if self.api and self.comment_id:
            return self.api.get_comment(self.comment_id)

    @comment.setter
    def comment(self, comment):
        if comment:
            self.comment_id = comment.id
