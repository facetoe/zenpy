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
        self._reopens = None
        self._assignee_stations = None
        self.assigned_at = None
        self._group_stations = None
        self.requester_updated_at = None
        self._replies = None
        self._requester_wait_time_in_minutes = None
        self.initially_assigned_at = None
        self._first_resolution_time_in_minutes = None
        self.id = None
        self.ticket_id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def on_hold_time_in_minutes(self):
        if self.api and self._on_hold_time_in_minutes:
            return self.api.get_ticket_metric_item(self._on_hold_time_in_minutes)

    @on_hold_time_in_minutes.setter
    def on_hold_time_in_minutes(self, on_hold_time_in_minutes):
        if on_hold_time_in_minutes:
            self._on_hold_time_in_minutes = on_hold_time_in_minutes

    @property
    def agent_wait_time_in_minutes(self):
        if self.api and self._agent_wait_time_in_minutes:
            return self.api.get_ticket_metric_item(self._agent_wait_time_in_minutes)

    @agent_wait_time_in_minutes.setter
    def agent_wait_time_in_minutes(self, agent_wait_time_in_minutes):
        if agent_wait_time_in_minutes:
            self._agent_wait_time_in_minutes = agent_wait_time_in_minutes

    @property
    def full_resolution_time_in_minutes(self):
        if self.api and self._full_resolution_time_in_minutes:
            return self.api.get_ticket_metric_item(self._full_resolution_time_in_minutes)

    @full_resolution_time_in_minutes.setter
    def full_resolution_time_in_minutes(self, full_resolution_time_in_minutes):
        if full_resolution_time_in_minutes:
            self._full_resolution_time_in_minutes = full_resolution_time_in_minutes

    @property
    def reply_time_in_minutes(self):
        if self.api and self._reply_time_in_minutes:
            return self.api.get_ticket_metric_item(self._reply_time_in_minutes)

    @reply_time_in_minutes.setter
    def reply_time_in_minutes(self, reply_time_in_minutes):
        if reply_time_in_minutes:
            self._reply_time_in_minutes = reply_time_in_minutes

    @property
    def requester_wait_time_in_minutes(self):
        if self.api and self._requester_wait_time_in_minutes:
            return self.api.get_ticket_metric_item(self._requester_wait_time_in_minutes)

    @requester_wait_time_in_minutes.setter
    def requester_wait_time_in_minutes(self, requester_wait_time_in_minutes):
        if requester_wait_time_in_minutes:
            self._requester_wait_time_in_minutes = requester_wait_time_in_minutes

    @property
    def first_resolution_time_in_minutes(self):
        if self.api and self._first_resolution_time_in_minutes:
            return self.api.get_ticket_metric_item(self._first_resolution_time_in_minutes)

    @first_resolution_time_in_minutes.setter
    def first_resolution_time_in_minutes(self, first_resolution_time_in_minutes):
        if first_resolution_time_in_minutes:
            self._first_resolution_time_in_minutes = first_resolution_time_in_minutes

    @property
    def ticket(self):
        if self.api and self.ticket_id:
            return self.api.get_ticket(self.ticket_id)

    @ticket.setter
    def ticket(self, ticket):
        if ticket:
            self.ticket_id = ticket.id
