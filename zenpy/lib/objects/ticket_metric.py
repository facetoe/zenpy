from zenpy.lib.objects.base_object import BaseObject


class TicketMetric(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.solved_at = None
        self._on_hold_time_in_minutes = None
        self._agent_wait_time_in_minutes = None
        self._full_resolution_time_in_minutes = None
        self.created_at = None
        self.status_updated_at = None
        self.updated_at = None
        self.latest_comment_added_at = None
        self._reply_time_in_minutes = None
        self.assignee_updated_at = None
        self.reopens = None
        self.assignee_stations = None
        self.assigned_at = None
        self.group_stations = None
        self.requester_updated_at = None
        self.replies = None
        self._requester_wait_time_in_minutes = None
        self.initially_assigned_at = None
        self._first_resolution_time_in_minutes = None
        self.id = None
        self.ticket_id = None

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
