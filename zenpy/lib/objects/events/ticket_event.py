from zenpy.lib.objects.base_object import BaseObject


class TicketEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.via = None
        self.child_events = None
        self.timestamp = None
        self.ticket_id = None
        self.id = None
        self.updater_id = None

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
    def updater(self):
        if self.api and self.updater_id:
            return self.api.get_user(self.updater_id)

    @updater.setter
    def updater(self, updater):
        if updater:
            self.updater_id = updater.id
