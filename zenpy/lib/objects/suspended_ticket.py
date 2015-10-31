from zenpy.lib.objects.base_object import BaseObject


class SuspendedTicket(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._via = None
        self._author = None
        self.url = None
        self.recipient = None
        self.created_at = None
        self.updated_at = None
        self.content = None
        self.brand_id = None
        self.ticket_id = None
        self.cause = None
        self.id = None
        self.subject = None

        for key, value in kwargs.iteritems():
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
    def brand(self):
        if self.api and self.brand_id:
            return self.api.get_brand(self.brand_id)

    @brand.setter
    def brand(self, brand):
        if brand:
            self.brand_id = brand.id

    @property
    def ticket(self):
        if self.api and self.ticket_id:
            return self.api.get_ticket(self.ticket_id)

    @ticket.setter
    def ticket(self, ticket):
        if ticket:
            self.ticket_id = ticket.id
