import logging

from zenpy.lib.api_objects import *
from zenpy.lib.api_objects.chat_objects import *
from zenpy.lib.cache import add_to_cache
from zenpy.lib.exception import ZenpyException
from zenpy.lib.util import as_singular, get_object_type

log = logging.getLogger(__name__)

__author__ = 'facetoe'


class ZendeskObjectMapping(object):
    """
    Handle converting Zendesk JSON objects to Python ones.
    """
    class_mapping = {
        'ticket': Ticket,
        'user': User,
        'organization': Organization,
        'group': Group,
        'brand': Brand,
        'topic': Topic,
        'comment': Comment,
        'attachment': Attachment,
        'thumbnail': Thumbnail,
        'metadata': Metadata,
        'system': System,
        'create': CreateEvent,
        'change': ChangeEvent,
        'notification': NotificationEvent,
        'voicecomment': VoiceCommentEvent,
        'commentprivacychange': CommentPrivacyChangeEvent,
        'satisfactionrating': SatisfactionRatingEvent,
        'ticketsharingevent': TicketSharingEvent,
        'organizationactivity': OrganizationActivityEvent,
        'error': ErrorEvent,
        'tweet': TweetEvent,
        'facebookevent': FacebookEvent,
        'facebookcomment': FacebookCommentEvent,
        'external': ExternalEvent,
        'logmeintranscript': LogmeinTranscriptEvent,
        'push': PushEvent,
        'cc': CcEvent,
        'via': Via,
        'source': Source,
        'job_status': JobStatus,
        'audit': Audit,
        'ticket_event': TicketEvent,
        'tag': Tag,
        'suspended_ticket': SuspendedTicket,
        'ticket_audit': TicketAudit,
        'satisfaction_rating': SatisfactionRating,
        'activity': Activity,
        'group_membership': GroupMembership,
        'ticket_metric': TicketMetric,
        'ticket_metric_event': TicketMetric,
        'status': Status,
        'ticket_metric_item': TicketMetricItem,
        'user_field': UserField,
        'organization_field': OrganizationField,
        'ticket_field': TicketField,
        'request': Request,
        'user_related': UserRelated,
        'organization_membership': OrganizationMembership,
        'upload': Upload,
        'sharing_agreement': SharingAgreement,
        'macro': Macro,
        'action': Action,
        'result': MacroResult,
        'job_status_result': JobStatusResult,
        'agentmacroreference': AgentMacroReference,
        'identity': Identity,
        'view': View,
        'conditions': Conditions,
        'view_row': ViewRow,
        'view_count': ViewCount,
        'export': Export,
        'sla_policy': SlaPolicy,
        'policy_metric': PolicyMetric,
        'definitions': Definitions
    }

    def __init__(self, api):
        self.api = api

    def object_from_json(self, object_type, object_json):
        """ 
        Given a blob of JSON representing a Zenpy object, recursively deserialize it and 
         any nested objects it contains. This method also adds the deserialized object
         to the relevant cache if applicable. 
        """
        if not isinstance(object_json, dict):
            return object_json
        ZenpyClass = self.class_for_type(object_type)
        obj = ZenpyClass(api=self.api)
        for key, value in object_json.items():
            if isinstance(value, dict):
                key = self.format_key(key, parent=obj)
                if key in self.class_mapping:
                    value = self.object_from_json(key, value)
                elif as_singular(key) in self.class_mapping:
                    value = self.object_from_json(as_singular(key), value)
            elif isinstance(value, list) and self.format_key(as_singular(key), parent=obj) in self.class_mapping:

                zenpy_objects = list()
                for item in value:
                    zenpy_objects.append(self.object_from_json(self.format_key(as_singular(key), parent=obj), item))
                value = zenpy_objects
            setattr(obj, key, value)
        add_to_cache(obj)
        return obj

    def class_for_type(self, object_type):
        """ Given an object_type return the class associated with it. """
        if object_type not in self.class_mapping:
            raise ZenpyException("Unknown object_type: " + str(object_type))
        else:
            return self.class_mapping[object_type]

    def format_key(self, key, parent):
        if key == 'result':
            key = "{}_result".format(get_object_type(parent))
        elif key in ('metadata', 'from', 'system', 'photo', 'thumbnails'):
            key = '{}'.format(key)
        return key


class ChatObjectMapping(ZendeskObjectMapping):
    """
    Handle converting Chat API objects to Python ones. This class exists
    mainly to prevent namespace collisions between the two APIs. 
    """
    class_mapping = {
        'chat': Chat,
        'offline_msg': OfflineMessage,
        'session': Session,
        'response_time': ResponseTime,
        'visitor': Visitor,
        'webpath': Webpath,
        'count': Count,
        'shortcut': Shortcut,
        'trigger': Trigger,
        'ban': Ban,
        'account': Account,
        'plan': Plan,
        'billing': Billing,
        'agent': Agent,
        'roles': Roles,
        'search_result': SearchResult,
        'ip_address': IpAddress,
        'department': Department,
        'goal': Goal
    }

    def __init__(self, api):
        super(ChatObjectMapping, self).__init__(api)
