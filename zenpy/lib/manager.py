from json import JSONEncoder
import logging

from cachetools import LRUCache, TTLCache

from zenpy.lib.exception import ZenpyException
from zenpy.lib.objects.activity import Activity
from zenpy.lib.objects.events.cc_event import CcEvent
from zenpy.lib.objects.events.change_event import ChangeEvent
from zenpy.lib.objects.events.comment_privacy_change_event import CommentPrivacyChangeEvent
from zenpy.lib.objects.events.error_event import ErrorEvent
from zenpy.lib.objects.events.external_event import ExternalEvent
from zenpy.lib.objects.events.facebook_comment_event import FacebookCommentEvent
from zenpy.lib.objects.events.facebook_event import FacebookEvent
from zenpy.lib.objects.events.logmein_transcript_event import LogmeinTranscriptEvent
from zenpy.lib.objects.events.organization_activity_event import OrganizationActivityEvent
from zenpy.lib.objects.events.push_event import PushEvent
from zenpy.lib.objects.events.satisfaction_rating_event import SatisfactionRatingEvent
from zenpy.lib.objects.events.ticket_event import TicketEvent
from zenpy.lib.objects.events.ticket_sharing_event import TicketSharingEvent
from zenpy.lib.objects.events.tweet_event import TweetEvent
from zenpy.lib.objects.group_membership import GroupMembership
from zenpy.lib.objects.organization_field import OrganizationField
from zenpy.lib.objects.satisfaction_rating import SatisfactionRating
from zenpy.lib.objects.status import Status
from zenpy.lib.objects.suspended_ticket import SuspendedTicket
from zenpy.lib.objects.tag import Tag
from zenpy.lib.objects.ticket_audit import TicketAudit
from zenpy.lib.objects.ticket_field import TicketField
from zenpy.lib.objects.ticket_metric import TicketMetric
from zenpy.lib.objects.ticket_metric_item import TicketMetricItem
from zenpy.lib.objects.user_field import UserField
from zenpy.lib.objects.via import Via
from zenpy.lib.objects.brand import Brand
from zenpy.lib.objects.group import Group
from zenpy.lib.objects.organization import Organization
from zenpy.lib.objects.ticket import Ticket
from zenpy.lib.objects.topic import Topic
from zenpy.lib.objects.user import User
from zenpy.lib.objects.attachment import Attachment
from zenpy.lib.objects.comment import Comment
from zenpy.lib.objects.thumbnail import Thumbnail
from zenpy.lib.objects.audit import Audit
from zenpy.lib.objects.events.create_event import CreateEvent
from zenpy.lib.objects.events.notification_event import NotificationEvent
from zenpy.lib.objects.job_status import JobStatus
from zenpy.lib.objects.metadata import Metadata
from zenpy.lib.objects.source import Source
from zenpy.lib.objects.system import System
from zenpy.lib.objects.events.voice_comment_event import VoiceCommentEvent

log = logging.getLogger(__name__)

__author__ = 'facetoe'


class ApiObjectEncoder(JSONEncoder):
    """ Class for encoding API objects"""

    def default(self, o):
        if hasattr(o, 'to_dict'):
            return o.to_dict()


class ClassManager(object):
    """
    ClassManager provides methods for converting JSON objects
    to the correct Python ones.
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
        'status': Status,
        'ticket_metric_item': TicketMetricItem,
        'user_field': UserField,
        'organization_field': OrganizationField,
        'ticket_field': TicketField
    }

    def __init__(self, api):
        self.api = api

    def object_from_json(self, object_type, object_json):
        obj = self._class_for_type(object_type)
        return self._object_from_json(obj, object_json)

    def _class_for_type(self, object_type):
        if object_type not in self.class_mapping:
            raise ZenpyException("Unknown object_type: " + str(object_type))
        else:
            return self.class_mapping[object_type]

    def _object_from_json(self, object_type, object_json):
        # This method is recursive, if we have already
        # created this object just return it.
        if not isinstance(object_json, dict):
            return object_json

        obj = object_type(api=self.api)
        for key, value in object_json.iteritems():
            if key in ('results', 'metadata', 'from', 'system', 'photo', 'thumbnails'):
                key = '_%s' % key

            if key in self.class_mapping.keys():
                value = self.object_from_json(key, value)
            setattr(obj, key, value)
        return obj


class ObjectManager(object):
    """
    The ObjectManager is responsible for maintaining various caches
    and also provides access to the ClassManager
    """

    user_cache = LRUCache(maxsize=200)
    organization_cache = LRUCache(maxsize=100)
    group_cache = LRUCache(maxsize=100)
    brand_cache = LRUCache(maxsize=100)
    ticket_cache = TTLCache(maxsize=100, ttl=30)
    ticket_field_cache = LRUCache(maxsize=100)
    comment_cache = TTLCache(maxsize=100, ttl=30)
    user_field_cache = LRUCache(maxsize=100)
    organization_field_cache = LRUCache(maxsize=100)

    def __init__(self, api):
        self.class_manager = ClassManager(api)
        self.cache_mapping = {
            'user': self.user_cache,
            'organization': self.organization_cache,
            'group': self.group_cache,
            'brand': self.brand_cache,
            'ticket': self.ticket_cache,
            'comment': self.comment_cache,
            'user_field': self.user_field_cache,
            'organization_field': self.organization_field_cache,
            'ticket_field': self.ticket_field_cache
        }

    def object_from_json(self, object_type, object_json):
        return self.class_manager.object_from_json(object_type, object_json)

    def delete_from_cache(self, obj):
        if isinstance(obj, list):
            for o in obj:
                self._delete_from_cache(o)
        else:
            self._delete_from_cache(obj)

    def _delete_from_cache(self, obj):
        object_type = obj.__class__.__name__.lower()
        cache = self.cache_mapping[object_type]
        obj = cache.pop(obj.id, None)
        if obj:
            log.debug("Cache RM: [%s %s]" % (object_type.capitalize(), obj.id))

    def query_cache(self, object_type, _id):
        if object_type not in self.cache_mapping.keys():
            return None

        cache = self.cache_mapping[object_type]
        if _id in cache:
            log.debug("Cache HIT: [%s %s]" % (object_type.capitalize(), _id))
            return cache[_id]
        else:
            log.debug('Cache MISS: [%s %s]' % (object_type.capitalize(), _id))

    def update_caches(self, _json):
        if 'results' in _json:
            self._cache_search_results(_json)
        else:
            for object_type in self.cache_mapping.keys():
                self._add_to_cache(object_type, _json)

    def _add_to_cache(self, object_type, object_json):
        cache = self.cache_mapping[object_type]
        multiple_key = object_type + 's'
        if object_type in object_json:
            obj = object_json[object_type]
            log.debug("Caching: [%s %s]" % (object_type.capitalize(), obj['id']))
            self._cache_item(cache, obj, object_type)

        elif multiple_key in object_json:
            objects = object_json[multiple_key]
            log.debug("Caching %s %s " % (len(objects), multiple_key.capitalize()))
            for obj in object_json[multiple_key]:
                self._cache_item(cache, obj, object_type)

    def _cache_search_results(self, _json):
        results = _json['results']
        log.debug("Caching %s search results" % len(results))
        for result in results:
            object_type = result['result_type']
            cache = self.cache_mapping[object_type]
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
