import dateutil.parser

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

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def solved(self):
        if self.solved_at:
            return dateutil.parser.parse(self.solved_at)

    @solved.setter
    def solved(self, solved):
        if solved:
            self.solved_at = solved

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
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created

    @property
    def status_updated(self):
        if self.status_updated_at:
            return dateutil.parser.parse(self.status_updated_at)

    @status_updated.setter
    def status_updated(self, status_updated):
        if status_updated:
            self.status_updated_at = status_updated

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated

    @property
    def latest_comment_added(self):
        if self.latest_comment_added_at:
            return dateutil.parser.parse(self.latest_comment_added_at)

    @latest_comment_added.setter
    def latest_comment_added(self, latest_comment_added):
        if latest_comment_added:
            self.latest_comment_added_at = latest_comment_added

    @property
    def reply_time_in_minutes(self):
        if self.api and self._reply_time_in_minutes:
            return self.api.get_ticket_metric_item(self._reply_time_in_minutes)

    @reply_time_in_minutes.setter
    def reply_time_in_minutes(self, reply_time_in_minutes):
        if reply_time_in_minutes:
            self._reply_time_in_minutes = reply_time_in_minutes

    @property
    def assignee_updated(self):
        if self.assignee_updated_at:
            return dateutil.parser.parse(self.assignee_updated_at)

    @assignee_updated.setter
    def assignee_updated(self, assignee_updated):
        if assignee_updated:
            self.assignee_updated_at = assignee_updated

    @property
    def assigned(self):
        if self.assigned_at:
            return dateutil.parser.parse(self.assigned_at)

    @assigned.setter
    def assigned(self, assigned):
        if assigned:
            self.assigned_at = assigned

    @property
    def requester_updated(self):
        if self.requester_updated_at:
            return dateutil.parser.parse(self.requester_updated_at)

    @requester_updated.setter
    def requester_updated(self, requester_updated):
        if requester_updated:
            self.requester_updated_at = requester_updated

    @property
    def requester_wait_time_in_minutes(self):
        if self.api and self._requester_wait_time_in_minutes:
            return self.api.get_ticket_metric_item(self._requester_wait_time_in_minutes)

    @requester_wait_time_in_minutes.setter
    def requester_wait_time_in_minutes(self, requester_wait_time_in_minutes):
        if requester_wait_time_in_minutes:
            self._requester_wait_time_in_minutes = requester_wait_time_in_minutes

    @property
    def initially_assigned(self):
        if self.initially_assigned_at:
            return dateutil.parser.parse(self.initially_assigned_at)

    @initially_assigned.setter
    def initially_assigned(self, initially_assigned):
        if initially_assigned:
            self.initially_assigned_at = initially_assigned

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
