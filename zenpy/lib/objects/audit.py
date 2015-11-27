import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Audit(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._via = None
        self.created_at = None
        self._events = None
        self.ticket_id = None
        self.author_id = None
        self.id = None
        self._metadata = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def via(self):
        if self.api and self._via:
            return self.api.get_via(self._via)

    @via.setter
    def via(self, via):
        if via:
            self._via = via

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created

    @property
    def events(self):
        if self.api and self._events:
            return self.api.get_events(self._events)

    @events.setter
    def events(self, events):
        if events:
            self._events = events

    @property
    def ticket(self):
        if self.api and self.ticket_id:
            return self.api.get_ticket(self.ticket_id)

    @ticket.setter
    def ticket(self, ticket):
        if ticket:
            self.ticket_id = ticket.id

    @property
    def author(self):
        if self.api and self.author_id:
            return self.api.get_user(self.author_id)

    @author.setter
    def author(self, author):
        if author:
            self.author_id = author.id

    @property
    def metadata(self):
        if self.api and self._metadata:
            return self.api.get_metadata(self._metadata)

    @metadata.setter
    def metadata(self, metadata):
        if metadata:
            self._metadata = metadata
