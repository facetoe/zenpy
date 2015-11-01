import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Topic(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.body = None
        self.locked = None
        self.title = None
        self.url = None
        self._search_phrases = None
        self.created_at = None
        self.tags = None
        self.forum_id = None
        self.updated_at = None
        self.submitter_id = None
        self.pinned = None
        self.topic_type = None
        self.position = None
        self.id = None
        self.updater_id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def search_phrases(self):
        if self.api and self._search_phrases:
            return self.api.get_search_phrases(self._search_phrases)

    @search_phrases.setter
    def search_phrases(self, search_phrases):
        if search_phrases:
            self._search_phrases = search_phrases

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created_at

    @property
    def tags(self):
        if self.api and self.tags:
            return self.api.get_tags(self.tags)

    @tags.setter
    def tags(self, tags):
        if tags:
            self.tags = tags

    @property
    def forum(self):
        if self.api and self.forum_id:
            return self.api.get_forum(self.forum_id)

    @forum.setter
    def forum(self, forum):
        if forum:
            self.forum_id = forum.id

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated_at

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
