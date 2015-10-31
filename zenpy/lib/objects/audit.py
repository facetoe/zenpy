from zenpy.lib.objects.base_object import BaseObject


class Audit(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._via = None
        self.created_at = None
        self.events = None
        self.ticket_id = None
        self.author_id = None
        self.id = None
        self._metadata = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

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
