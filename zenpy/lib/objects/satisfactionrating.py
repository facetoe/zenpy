import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class SatisfactionRating(BaseObject):
    def __init__(self, api=None, score=None, comment=None):
        self.api = api
        self.url = None
        self.created_at = None
        self._created = None
        self.updated_at = None
        self._updated = None
        self._assignee = None
        self.assignee_id = None
        self.score = score
        self.comment = comment
        self._ticket = None
        self.ticket_id = None
        self._requester = None
        self.requester_id = None
        self._group = None
        self.group_id = None
        self.id = None

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, value):
        self._created = value

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, value):
        self._updated = value

    @property
    def assignee(self):
        if self.api and self.assignee_id:
            return self.api.get_user(self.assignee_id)

    @assignee.setter
    def assignee(self, value):
        self._assignee = value

    @property
    def ticket(self):
        if self.api and self.ticket_id:
            return self.api.get_ticket(self.ticket_id)

    @ticket.setter
    def ticket(self, value):
        self._ticket = value

    @property
    def requester(self):
        if self.api and self.requester_id:
            return self.api.get_user(self.requester_id)

    @requester.setter
    def requester(self, value):
        self._requester = value

    @property
    def group(self):
        if self.api and self.group_id:
            return self.api.get_group(self.group_id)

    @group.setter
    def group(self, value):
        self._group = value
