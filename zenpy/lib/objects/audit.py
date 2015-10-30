import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Audit(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self.via = None
        self.created_at = None
        self._events = None
        self.ticket = None
        self.ticket_id = None
        self._author = None
        self.author_id = None
        self.id = None
        self.metadata = None
        self._metadata = None

    @property
    def events(self):
        if self.api and self._events:
            for event in self._events:
                yield self.api.object_manager.object_from_json(event['type'].lower(), event)

    @events.setter
    def events(self, value):
        self._events = value

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, value):
        self._created = value

    @property
    def ticket(self):
        if self.api and self.ticket_id:
            return self.api.get_ticket(self.ticket_id)

    @ticket.setter
    def ticket(self, value):
        self._ticket = value

    @property
    def author(self):
        if self.api and self.author_id:
            return self.api.get_user(self.author_id)

    @author.setter
    def author(self, value):
        self._author = value

    @property
    def metadata(self):
        if self.api and self._metadata:
            return self.api.object_manager.object_from_json('metadata', self._metadata)

    @metadata.setter
    def metadata(self, value):
        self._metadata = value
