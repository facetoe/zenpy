import logging

import zenpy
from zenpy.lib.api_objects import *
from zenpy.lib.api_objects.chat_objects import *
from zenpy.lib.api_objects.help_centre_objects import Article, Category, Section, Label, Translation, Topic, Post, \
    Subscription, Vote, AccessPolicy, UserSegment
from zenpy.lib.api_objects.talk_objects import *
from zenpy.lib.exception import ZenpyException
from zenpy.lib.proxy import ProxyDict, ProxyList
from zenpy.lib.util import as_singular, get_object_type

log = logging.getLogger(__name__)

__author__ = 'facetoe'


class ZendeskObjectMapping(object):
    """
    Handle converting Zendesk Support JSON objects to Python ones.
    """
    class_mapping = {
        'ticket': Ticket,
        'deleted_ticket': Ticket,
        'user': User,
        'deleted_user': User,
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
        'ticket_metric_event': TicketMetricEvent,
        'status': Status,
        'ticket_metric_item': TicketMetricItem,
        'user_field': UserField,
        'organization_field': OrganizationField,
        'ticket_field': TicketField,
        'ticket_form': TicketForm,
        'request': Request,
        'user_related': UserRelated,
        'organization_membership': OrganizationMembership,
        'upload': Upload,
        'sharing_agreement': SharingAgreement,
        'macro': Macro,
        'result': MacroResult,
        'macro_attachment': MacroAttachment,
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
        'definitions': Definitions,
        'recipient_address': RecipientAddress,
        'recipient': Recipient,
        'response': Response,
        'trigger': zenpy.lib.api_objects.Trigger,
        'automation': Automation,
        'item': Item,
        'target': Target,
        'locale': Locale,
        'custom_field_option': CustomFieldOption,
        'variant': Variant,
        'link': Link,
        'skip': Skip,
        'schedule': Schedule,
        'custom_role': CustomAgentRole
    }

    skip_attrs = []
    always_dirty = {}

    def __init__(self, api):
        self.api = api
        self.skip_attrs = ['user_fields', 'organization_fields']
        self.always_dirty = dict(
            conditions=('all', 'any'),
            organization_field=('custom_field_options',),
            ticket_field=('custom_field_options',),
            user=('name',)
        )

    def object_from_json(self, object_type, object_json, parent=None):
        """
        Given a blob of JSON representing a Zenpy object, recursively deserialize it and
         any nested objects it contains. This method also adds the deserialized object
         to the relevant cache if applicable.
        """
        if not isinstance(object_json, dict):
            return object_json
        obj = self.instantiate_object(object_type, parent)
        for key, value in object_json.items():
            if key not in self.skip_attrs:
                key, value = self._deserialize(key, obj, value)
            if isinstance(value, dict):
                value = ProxyDict(value, dirty_callback=getattr(
                    obj, '_dirty_callback', None))
            elif isinstance(value, list):
                value = ProxyList(value, dirty_callback=getattr(
                    obj, '_dirty_callback', None))
            setattr(obj, key, value)
        if hasattr(obj, '_clean_dirty'):
            obj._clean_dirty()
        self.api.cache.add(obj)
        return obj

    def instantiate_object(self, object_type, parent):
        """
        Instantiate a Zenpy object. If this object has a parent, add a callback to call the parent if it is modified.
        This is so the parent object is correctly marked as dirty when a child is modified, eg:

            view.conditions.all.append(<something>)

        Also, some attributes need to be sent together to Zendesk together if either is modified. For example,
        Condition objects need to send both "all" and "any", even if only one has changed. If we have such values
        configured, add them. They will be inspected in the objects to_dict method on serialization.
        """
        ZenpyClass = self.class_for_type(object_type)
        obj = ZenpyClass(api=self.api)
        if parent:
            def dirty_callback():
                parent._dirty = True
                obj._dirty = True

            obj._dirty_callback = dirty_callback
        obj._always_dirty.update(self.always_dirty.get(object_type, []))
        return obj

    def _deserialize(self, key, obj, value):
        if isinstance(value, dict):
            key = self.format_key(key, parent=obj)
            if key in self.class_mapping:
                value = self.object_from_json(key, value, parent=obj)
            elif as_singular(key) in self.class_mapping:
                value = self.object_from_json(
                    as_singular(key), value, parent=obj)
        elif isinstance(value, list) and self.format_key(as_singular(key), parent=obj) in self.class_mapping:
            zenpy_objects = list()
            for item in value:
                object_type = self.format_key(as_singular(key), parent=obj)
                zenpy_objects.append(self.object_from_json(
                    object_type, item, parent=obj))
            value = zenpy_objects
        return key, value

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
    to prevent namespace collisions between APIs.
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
        'trigger': zenpy.lib.api_objects.chat_objects.Trigger,
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


class HelpCentreObjectMapping(ZendeskObjectMapping):
    """
    Handle converting Helpdesk API objects to Python ones. This class exists
    to prevent namespace collisions between APIs.
    """
    class_mapping = {
        'article': Article,
        'category': Category,
        'section': Section,
        'comment': zenpy.lib.api_objects.help_centre_objects.Comment,
        'article_attachment': zenpy.lib.api_objects.help_centre_objects.ArticleAttachment,
        'label': Label,
        'translation': Translation,
        'topic': zenpy.lib.api_objects.help_centre_objects.Topic,
        'post': Post,
        'subscription': Subscription,
        'vote': Vote,
        'access_policy': AccessPolicy,
        'user_segment': UserSegment
    }

class TalkObjectMapping(ZendeskObjectMapping):
    """
    Handle converting Talk API objects to Python ones. This class exists
    to prevent namespace collisions between APIs.
    """
    class_mapping = {
        'account_overview': AccountOverview,
        'agents_activity': AgentsActivity,
        'agents_overview': AgentsOverview,
        'current_queue_activity': CurrentQueueActivity,
        'phone_numbers': PhoneNumbers,
        'availability': ShowAvailability
    }
