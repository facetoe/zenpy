from zenpy.lib.objects.base_object import BaseObject


class SatisfactionRatingEvent(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._assignee = None
        self.assignee_id = None
        self.body = None
        self.score = None
        self.type = None
        self.id = None

    @property
    def assignee(self):
        if self.api and self.assignee_id:
            return self.api.get_user(self.assignee_id)

    @assignee.setter
    def assignee(self, value):
        self._assignee = value
