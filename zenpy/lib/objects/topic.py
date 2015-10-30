import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Topic(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.body = None
        self.locked = None
        self.title = None
        self.url = None
        self.search_phrases = None
        self.created_at = None
        self.tags = None
        self._forum = None
        self.forum_id = None
        self.updated_at = None
        self._submitter = None
        self.submitter_id = None
        self.pinned = None
        self.topic_type = None
        self.position = None
        self.id = None
        self._updater = None
        self.updater_id = None

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, value):
        self._created = value

    @property
    def forum(self):
        if self.api and self.forum_id:
            return self.api.get_forum(self.forum_id)

    @forum.setter
    def forum(self, value):
        self._forum = value

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, value):
        self._updated = value

    @property
    def submitter(self):
        if self.api and self.submitter_id:
            return self.api.get_user(self.submitter_id)

    @submitter.setter
    def submitter(self, value):
        self._submitter = value

    @property
    def updater(self):
        if self.api and self.updater_id:
            return self.api.get_updater(self.updater_id)

    @updater.setter
    def updater(self, value):
        self._updater = value
