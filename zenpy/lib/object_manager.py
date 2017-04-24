import logging

from lib.api_objects.chat_objects import Chat, Session, ResponseTime, Visitor, Webpath
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
from zenpy.lib.cache import add_to_cache
from zenpy.lib.exception import ZenpyException

log = logging.getLogger(__name__)

__author__ = 'facetoe'

# Dictionary for mapping object types to Python classes
ZENDESK_CLASS_MAPPING = {
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

CHAT_CLASS_MAPPING = {
    'chat': Chat,
    'session': Session,
    'response_time': ResponseTime,
    'visitor': Visitor,
    'webpath': Webpath,

}


def class_for_type(object_type, is_chat_api=False):
    """ Given an object_type return the class associated with it. """
    class_mapping = _get_class_mapping(is_chat_api)
    if object_type not in class_mapping:
        raise ZenpyException("Unknown object_type: " + str(object_type))
    else:
        return class_mapping[object_type]


def object_from_json(api, object_type, object_json, is_chat_api=False):
    """ 
    Given a blob of JSON representing a Zenpy object, recursively deserialize it and 
     any nested objects it contains. 
    """
    if not isinstance(object_json, dict):
        return
    ZenpyClass = class_for_type(object_type, is_chat_api=is_chat_api)
    obj = ZenpyClass(api=api)
    for key, value in object_json.items():
        key = format_key(key, is_chat_api)
        if key in _get_class_mapping(is_chat_api):
            print(key, value)
            value = object_from_json(api, key, value, is_chat_api=is_chat_api)
        setattr(obj, key, value)
    add_to_cache(obj)
    return obj


def format_key(key, is_chat_api):
    if is_chat_api:
        if key in ('webpath',):
            key = '_{}'.format(key)
    elif key in ('metadata', 'from', 'system', 'photo', 'thumbnails'):
        key = '{}'.format(key)
    return key


def _get_class_mapping(is_chat_api):
    """ Return the correct class mapping for the current API. """
    class_mapping = ZENDESK_CLASS_MAPPING
    if is_chat_api:
        class_mapping = CHAT_CLASS_MAPPING
    return class_mapping
