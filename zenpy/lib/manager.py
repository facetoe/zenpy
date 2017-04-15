import logging

import re

from datetime import datetime, date
from json import JSONEncoder

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
from zenpy.lib.cache import ZenpyCache
from zenpy.lib.exception import ZenpyException
from zenpy.lib.util import to_snake_case

log = logging.getLogger(__name__)

__author__ = 'facetoe'

# Dict for mapping object types to Python classes
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

# Dict for managing default object caches
cache_mapping = {
    'user': ZenpyCache('LRUCache', maxsize=10000),
    'organization': ZenpyCache('LRUCache', maxsize=10000),
    'group': ZenpyCache('LRUCache', maxsize=10000),
    'brand': ZenpyCache('LRUCache', maxsize=10000),
    'ticket': ZenpyCache('TTLCache', maxsize=10000, ttl=30),
    'comment': ZenpyCache('LRUCache', maxsize=10000),
    'request': ZenpyCache('LRUCache', maxsize=10000),
    'user_field': ZenpyCache('TTLCache', maxsize=10000, ttl=30),
    'organization_field': ZenpyCache('LRUCache', maxsize=10000),
    'ticket_field': ZenpyCache('LRUCache', maxsize=10000),
    'sharing_agreement': ZenpyCache('TTLCache', maxsize=10000, ttl=6000),
    'identity': ZenpyCache('LRUCache', maxsize=10000)
}


def class_for_type(object_type):
    if object_type not in class_mapping:
        raise ZenpyException("Unknown object_type: " + str(object_type))
    else:
        return class_mapping[object_type]


class ApiObjectEncoder(JSONEncoder):
    """ Class for encoding API objects"""

    def default(self, o):
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        elif isinstance(o, datetime):
            return o.date().isoformat()
        elif isinstance(o, date):
            return o.isoformat()


class ObjectManager(object):
    """
    The ObjectManager is responsible for maintaining various caches
    and converting the JSON returned from Zendesk to Python objects.
    """

    def __init__(self, api):
        self.api = api

    def object_from_json(self, object_type, object_json):
        if not isinstance(object_json, dict):
            return
        ZenpyClass = class_for_type(object_type)
        obj = ZenpyClass(api=self.api)
        for key, value in object_json.items():
            if key in ('metadata', 'from', 'system', 'photo', 'thumbnails'):
                key = '_%s' % key
            if key in class_mapping:
                value = self.object_from_json(key, value)
            setattr(obj, key, value)
        return obj

    def update_caches(self, _json):
        if 'results' in _json:
            self._cache_search_results(_json)
        else:
            for object_type in cache_mapping:
                self._add_to_cache(object_type, _json)

    def delete_from_cache(self, obj):
        if isinstance(obj, list):
            for o in obj:
                self._delete_from_cache(o)
        else:
            self._delete_from_cache(obj)

    def _delete_from_cache(self, obj):
        object_type = to_snake_case(obj.__class__.__name__)
        if object_type in cache_mapping:
            cache = cache_mapping[object_type]
            obj = cache.pop(obj.id, None)
            if obj:
                log.debug("Cache RM: [%s %s]" % (object_type.capitalize(), obj.id))

    def query_cache(self, object_type, _id):
        if object_type not in cache_mapping:
            return None

        cache = cache_mapping[object_type]
        if _id in cache:
            log.debug("Cache HIT: [%s %s]" % (object_type.capitalize(), _id))
            return cache[_id]
        else:
            log.debug('Cache MISS: [%s %s]' % (object_type.capitalize(), _id))

    def _add_to_cache(self, object_type, object_json):
        cache = cache_mapping[object_type]
        if object_type in object_json:
            obj = object_json[object_type]
            log.debug("Caching: [%s %s]" % (object_type.capitalize(), obj['id']))
            self._cache_item(cache, obj, object_type)

        else:
            # When collections are returned they are returned in the plural form (eg, users, identities)
            # We can only guess at the correct form and then attempt to locate it in the JSON.
            multiple_keys = (object_type + 's', re.sub('y$', 'ies', object_type))
            for plural_key in multiple_keys:
                if plural_key in object_json:
                    objects = object_json[plural_key]
                    log.debug("Caching %s %s " % (len(objects), plural_key.capitalize()))
                    for obj in object_json[plural_key]:
                        self._cache_item(cache, obj, object_type)

    def _cache_search_results(self, _json):
        results = _json['results']
        log.debug("Caching %s search results" % len(results))
        for result in results:
            object_type = result['result_type']
            cache = cache_mapping[object_type]
            self._cache_item(cache, result, object_type)

    def _cache_item(self, cache, item_json, item_type):
        key = self.get_key(item_type)
        cache[item_json[key]] = self.object_from_json(item_type, item_json)

    def get_key(self, item_type):
        if item_type in ('user_field', 'organization_field'):
            key = 'key'
        else:
            key = 'id'
        return key
