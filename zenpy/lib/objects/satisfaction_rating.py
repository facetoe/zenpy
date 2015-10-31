from zenpy.lib.objects.base_object import BaseObject


class SatisfactionRating(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.url = None
        self.created_at = None
        self.updated_at = None
        self.assignee_id = None
        self.score = None
        self.ticket_id = None
        self.requester_id = None
        self.group_id = None
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

    @property
    def ticket(self):
        if self.api and self.ticket_id:
            return self.api.get_ticket(self.ticket_id)

    @ticket.setter
    def ticket(self, ticket):
        if ticket:
            self.ticket_id = ticket.id

    @property
    def requester(self):
        if self.api and self.requester_id:
            return self.api.get_user(self.requester_id)

    @requester.setter
    def requester(self, requester):
        if requester:
            self.requester_id = requester.id

    @property
    def group(self):
        if self.api and self.group_id:
            return self.api.get_group(self.group_id)

    @group.setter
    def group(self, group):
        if group:
            self.group_id = group.id
