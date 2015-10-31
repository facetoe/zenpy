from zenpy.lib.objects.base_object import BaseObject


class Topic(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._body = None
        self.locked = None
        self._title = None
        self._url = None
        self._search_phrases = None
        self.created_at = None
        self.tags = None
        self.forum_id = None
        self.updated_at = None
        self.submitter_id = None
        self.pinned = None
        self._topic_type = None
        self._position = None
        self.id = None
        self.updater_id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def forum(self):
        if self.api and self.forum_id:
            return self.api.get_forum(self.forum_id)

    @forum.setter
    def forum(self, forum):
        if forum:
            self.forum_id = forum.id

    @property
    def submitter(self):
        if self.api and self.submitter_id:
            return self.api.get_user(self.submitter_id)

    @submitter.setter
    def submitter(self, submitter):
        if submitter:
            self.submitter_id = submitter.id

    @property
    def updater(self):
        if self.api and self.updater_id:
            return self.api.get_user(self.updater_id)

    @updater.setter
    def updater(self, updater):
        if updater:
            self.updater_id = updater.id
