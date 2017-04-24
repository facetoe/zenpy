import logging

from zenpy.lib.api_objects import Activity, Request, UserRelated, OrganizationMembership, Upload, SharingAgreement, \
    Macro, Action, MacroResult, AgentMacroReference, Identity
from zenpy.lib.api_objects import Attachment
from zenpy.lib.api_objects import Audit
from zenpy.lib.api_objects import Brand
from zenpy.lib.api_objects import CcEvent
from zenpy.lib.api_objects import ChangeEvent
from zenpy.lib.api_objects import Comment
from zenpy.lib.api_objects import CommentPrivacyChangeEvent
from zenpy.lib.api_objects import CreateEvent
from zenpy.lib.api_objects import ErrorEvent
from zenpy.lib.api_objects import ExternalEvent
from zenpy.lib.api_objects import FacebookCommentEvent
from zenpy.lib.api_objects import FacebookEvent
from zenpy.lib.api_objects import Group
from zenpy.lib.api_objects import GroupMembership
from zenpy.lib.api_objects import JobStatus
from zenpy.lib.api_objects import LogmeinTranscriptEvent
from zenpy.lib.api_objects import Metadata
from zenpy.lib.api_objects import NotificationEvent
from zenpy.lib.api_objects import Organization
from zenpy.lib.api_objects import OrganizationActivityEvent
from zenpy.lib.api_objects import OrganizationField
from zenpy.lib.api_objects import PushEvent
from zenpy.lib.api_objects import SatisfactionRating
from zenpy.lib.api_objects import SatisfactionRatingEvent
from zenpy.lib.api_objects import Source
from zenpy.lib.api_objects import Status
from zenpy.lib.api_objects import SuspendedTicket
from zenpy.lib.api_objects import System
from zenpy.lib.api_objects import Tag
from zenpy.lib.api_objects import Thumbnail
from zenpy.lib.api_objects import Ticket
from zenpy.lib.api_objects import TicketAudit
from zenpy.lib.api_objects import TicketEvent
from zenpy.lib.api_objects import TicketField
from zenpy.lib.api_objects import TicketMetric
from zenpy.lib.api_objects import TicketMetricItem
from zenpy.lib.api_objects import TicketSharingEvent
from zenpy.lib.api_objects import Topic
from zenpy.lib.api_objects import TweetEvent
from zenpy.lib.api_objects import User
from zenpy.lib.api_objects import UserField
from zenpy.lib.api_objects import Via
from zenpy.lib.api_objects import VoiceCommentEvent
from zenpy.lib.api_objects.chat_objects import Chat, Session, ResponseTime, Visitor, Webpath, Count, OfflineMessage, \
    Shortcut, Trigger, Ban, Account, Plan, Billing
from zenpy.lib.cache import add_to_cache
from zenpy.lib.exception import ZenpyException

log = logging.getLogger(__name__)

__author__ = 'facetoe'


class ZendeskDeserializer(object):
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
        'agentmacroreference': AgentMacroReference,
        'identity': Identity
    }

    def __init__(self, api):
        self.api = api

    def object_from_json(self, object_type, object_json):
        """ 
        Given a blob of JSON representing a Zenpy object, recursively deserialize it and 
         any nested objects it contains. 
        """
        if not isinstance(object_json, dict):
            return
        ZenpyClass = self.class_for_type(object_type)
        obj = ZenpyClass(api=self.api)
        for key, value in object_json.items():
            if isinstance(value, dict):
                key = self.format_key(key)
                if key in self.class_mapping:
                    value = self.object_from_json(key, value)
            setattr(obj, key, value)
        add_to_cache(obj)
        return obj

    def class_for_type(self, object_type):
        """ Given an object_type return the class associated with it. """
        if object_type not in self.class_mapping:
            raise ZenpyException("Unknown object_type: " + str(object_type))
        else:
            return self.class_mapping[object_type]

    def format_key(self, key):
        if key in ('metadata', 'from', 'system', 'photo', 'thumbnails'):
            key = '{}'.format(key)
        return key


class ChatDeserializer(ZendeskDeserializer):
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
        'billing': Billing
    }

    def __init__(self, api):
        super(ChatDeserializer, self).__init__(api)

    def format_key(self, key):
        if key in ('webpath',):
            key = '_{}'.format(key)
        return key
