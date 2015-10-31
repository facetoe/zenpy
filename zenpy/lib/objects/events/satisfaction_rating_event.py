from zenpy.lib.objects.base_object import BaseObject


class SatisfactionRatingEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.assignee_id = None
        self.body = None
        self.score = None
        self.type = None
        self.id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def assignee(self):
        if self.api and self.assignee_id:
            return self.api.get_user(self.assignee_id)

    @assignee.setter
    def assignee(self, assignee):
        if assignee:
            self.assignee_id = assignee.id
