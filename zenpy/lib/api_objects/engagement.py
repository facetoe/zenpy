from zenpy.lib.api_objects import BaseObject

class Engagement(BaseObject):
    def __init__(
        self,
        engagement_id=None,
        ticket_id=None,
        agent_id=None,
        group_id=None,
        requester_id=None,
        offer_time_seconds=None,
        assignment_to_first_reply_time_seconds=None,
        average_requester_wait_time_seconds=None,
        agent_messages_count=None,
        agent_replies_count=None,
        total_requester_wait_time_seconds=None,
        longest_requester_wait_time_seconds=None,
        channel=None,
        engagement_start_reason=None,
        engagement_start_time=None,
        engagement_end_time=None,
        ticket_status_start=None,
        ticket_status_end=None,
        engagement_end_reason=None,
        end_user_messages_count=None,
        api=None,
        **kwargs
    ):
        self.engagement_id = engagement_id
        self.ticket_id = ticket_id
        self.agent_id = agent_id
        self.group_id = group_id
        self.requester_id = requester_id
        self.offer_time_seconds = offer_time_seconds
        self.assignment_to_first_reply_time_seconds = assignment_to_first_reply_time_seconds
        self.average_requester_wait_time_seconds = average_requester_wait_time_seconds
        self.agent_messages_count = agent_messages_count
        self.agent_replies_count = agent_replies_count
        self.total_requester_wait_time_seconds = total_requester_wait_time_seconds
        self.longest_requester_wait_time_seconds = longest_requester_wait_time_seconds
        self.channel = channel
        self.engagement_start_reason = engagement_start_reason
        self.engagement_start_time = engagement_start_time
        self.engagement_end_time = engagement_end_time
        self.ticket_status_start = ticket_status_start
        self.ticket_status_end = ticket_status_end
        self.engagement_end_reason = engagement_end_reason
        self.end_user_messages_count = end_user_messages_count
        
        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue
                    