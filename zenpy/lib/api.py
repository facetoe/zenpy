# coding=utf-8

import json
import logging
from time import sleep, time

from zenpy.lib.api_objects import (
    User,
    Macro,
    Identity,
    View,
    Organization,
    Group,
    GroupMembership,
    OrganizationField,
    TicketField,
    Comment as TicketComment,
    CustomFieldOption,
    Item, Variant, Ticket, BaseObject)
from zenpy.lib.api_objects.help_centre_objects import (
    Section,
    Article,
    Comment,
    ArticleAttachment,
    Label,
    Category,
    Translation,
    Topic,
    Post,
    Subscription
)
from zenpy.lib.api_objects.talk_objects import (
    CurrentQueueActivity,
    PhoneNumbers,
    ShowAvailability,
    AgentsOverview,
    AccountOverview,
    AgentsActivity
)
from zenpy.lib.exception import *
from zenpy.lib.mapping import ZendeskObjectMapping, ChatObjectMapping, HelpCentreObjectMapping, TalkObjectMapping
from zenpy.lib.request import *
from zenpy.lib.response import *
from zenpy.lib.util import as_plural, extract_id, is_iterable_but_not_string, json_encode_for_zendesk

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

__author__ = 'facetoe'

log = logging.getLogger(__name__)


class BaseApi(object):
    """
    Base class for API. Responsible for submitting requests to Zendesk, controlling
    rate limiting and deserializing responses.
    """

    def __init__(self, subdomain, session, timeout, ratelimit, ratelimit_budget, ratelimit_request_interval, cache):
        self.domain = 'zendesk.com'
        self.subdomain = subdomain
        self.session = session
        self.timeout = timeout
        self.ratelimit = ratelimit
        self.ratelimit_budget = ratelimit_budget
        self.cache = cache
        self.protocol = 'https'
        self.api_prefix = 'api/v2'
        self._url_template = "%(protocol)s://%(subdomain)s.zendesk.com/%(api_prefix)s"
        self.callsafety = {
            'lastcalltime': None,
            'lastlimitremaining': None
        }
        self.ratelimit_request_interval = ratelimit_request_interval
        self._response_handlers = (
            DeleteResponseHandler,
            TagResponseHandler,
            SearchResponseHandler,
            JobStatusesResponseHandler,
            CombinationResponseHandler,
            ViewResponseHandler,
            SlaPolicyResponseHandler,
            RequestCommentResponseHandler,
            GenericZendeskResponseHandler,
            HTTPOKResponseHandler,
        )
        # An object is considered dirty when it has modifications. We want to ensure that it is successfully
        # accepted by Zendesk before cleaning it's dirty attributes, so we store it here until the response
        # is successfully processed, and then call the objects _clean_dirty() method.
        self._dirty_object = None

    def _post(self, url, payload, content_type=None, **kwargs):
        if 'data' in kwargs:
            if content_type:
                headers = {'Content-Type': content_type}
            else:
                headers = {'Content-Type': 'application/octet-stream'}
        else:
            headers = None
        response = self._call_api(self.session.post, url,
                                  json=self._serialize(payload),
                                  timeout=self.timeout,
                                  headers=headers,
                                  **kwargs)
        return self._process_response(response)

    def _put(self, url, payload):
        response = self._call_api(self.session.put, url, json=self._serialize(payload), timeout=self.timeout)
        return self._process_response(response)

    def _delete(self, url, payload=None):
        response = self._call_api(self.session.delete, url, json=payload, timeout=self.timeout)
        return self._process_response(response)

    def _get(self, url, raw_response=False, **kwargs):
        response = self._call_api(self.session.get, url, timeout=self.timeout, **kwargs)
        if raw_response:
            return response
        else:
            return self._process_response(response)

    def _call_api(self, http_method, url, **kwargs):
        """
        Execute a call to the Zendesk API. Handles rate limiting, checking the response
        from Zendesk and deserialization of the Zendesk response. All
        communication with Zendesk should go through this method.

        :param http_method: The requests method to call (eg post, put, get).
        :param url: The url to pass to to the requests method.
        :param kwargs: Any additional kwargs to pass on to requests.
        """
        log.debug("{}: {} - {}".format(http_method.__name__.upper(), url, kwargs))
        if self.ratelimit is not None:
            # This path indicates we're taking a proactive approach to not hit the rate limit
            response = self._ratelimit(http_method=http_method, url=url, **kwargs)
        else:
            response = http_method(url, **kwargs)

        # If we are being rate-limited, wait the required period before trying again.
        if response.status_code == 429:
            while 'retry-after' in response.headers and int(response.headers['retry-after']) > 0:
                retry_after_seconds = int(response.headers['retry-after'])
                log.warning(
                    "Waiting for requested retry-after period: %s seconds" % retry_after_seconds
                )
                while retry_after_seconds > 0:
                    retry_after_seconds -= 1
                    self.check_ratelimit_budget(1)
                    log.debug("    -> sleeping: %s more seconds" % retry_after_seconds)
                    sleep(1)
                response = http_method(url, **kwargs)

        self._check_response(response)
        self._update_callsafety(response)
        return response

    def check_ratelimit_budget(self, seconds_waited):
        """ If we have a ratelimit_budget, ensure it is not exceeded. """
        if self.ratelimit_budget is not None:
            self.ratelimit_budget -= seconds_waited
            if self.ratelimit_budget < 1:
                raise RatelimitBudgetExceeded("Rate limit budget exceeded!")

    def _ratelimit(self, http_method, url, **kwargs):
        """ Ensure we do not hit the rate limit. """

        def time_since_last_call():
            if self.callsafety['lastcalltime'] is not None:
                return int(time() - self.callsafety['lastcalltime'])
            else:
                return None

        lastlimitremaining = self.callsafety['lastlimitremaining']

        if time_since_last_call() is None or time_since_last_call() >= self.ratelimit_request_interval or \
                lastlimitremaining >= self.ratelimit:
            response = http_method(url, **kwargs)
        else:
            # We hit our limit floor and aren't quite at ratelimit_request_interval value in seconds yet..
            log.warning(
                "Safety Limit Reached of %s remaining calls and time since last call is under %s seconds"
                % (self.ratelimit, self.ratelimit_request_interval)
            )
            while time_since_last_call() < self.ratelimit_request_interval:
                remaining_sleep = int(self.ratelimit_request_interval - time_since_last_call())
                log.debug("  -> sleeping: %s more seconds" % remaining_sleep)
                self.check_ratelimit_budget(1)
                sleep(1)
            response = http_method(url, **kwargs)

        self.callsafety['lastcalltime'] = time()
        self.callsafety['lastlimitremaining'] = int(response.headers.get('X-Rate-Limit-Remaining', 0))
        return response

    def _update_callsafety(self, response):
        """ Update the callsafety data structure """
        if self.ratelimit is not None:
            self.callsafety['lastcalltime'] = time()
            self.callsafety['lastlimitremaining'] = int(response.headers.get('X-Rate-Limit-Remaining', 0))

    def _process_response(self, response, object_mapping=None):
        """
        Attempt to find a ResponseHandler that knows how to process this response.
        If no handler can be found, raise an Exception.
        """
        try:
            pretty_response = response.json()
        except ValueError:
            pretty_response = response
        for handler in self._response_handlers:
            if handler.applies_to(self, response):
                log.debug("{} matched: {}".format(handler.__name__, pretty_response))
                r = handler(self, object_mapping).build(response)
                self._clean_dirty_objects()
                return r
        raise ZenpyException("Could not handle response: {}".format(pretty_response))

    def _clean_dirty_objects(self):
        """
        Clear all dirty attributes for the last object or list of objects successfully submitted to Zendesk.
        """
        if self._dirty_object is None:
            return
        if not is_iterable_but_not_string(self._dirty_object):
            self._dirty_object = [self._dirty_object]

        log.debug("Cleaning objects: {}".format(self._dirty_object))
        for o in self._dirty_object:
            if isinstance(o, BaseObject):
                o._clean_dirty()
        self._dirty_object = None

    def _serialize(self, zenpy_object):
        """ Serialize a Zenpy object to JSON """
        # If it's a dict this object has already been serialized.
        if not type(zenpy_object) == dict:
            log.debug("Setting dirty object: {}".format(zenpy_object))
            self._dirty_object = zenpy_object
        return json.loads(json.dumps(zenpy_object, default=json_encode_for_zendesk))

    def _query_zendesk(self, endpoint, object_type, *endpoint_args, **endpoint_kwargs):
        """
        Query Zendesk for items. If an id or list of ids are passed, attempt to locate these items
         in the relevant cache. If they cannot be found, or no ids are passed, execute a call to Zendesk
         to retrieve the items.

        :param endpoint: target endpoint.
        :param object_type: object type we are expecting.
        :param endpoint_args: args for endpoint
        :param endpoint_kwargs: kwargs for endpoint

        :return: either a ResultGenerator or a Zenpy object.
        """

        _id = endpoint_kwargs.get('id', None)
        if _id:
            item = self.cache.get(object_type, _id)
            if item:
                return item
            else:
                return self._get(url=self._build_url(endpoint(*endpoint_args, **endpoint_kwargs)))
        elif 'ids' in endpoint_kwargs:
            cached_objects = []
            # Check to see if we have all objects in the cache.
            # If we are missing even one we request them all again.
            # This could be optimized to only request the missing objects.
            for _id in endpoint_kwargs['ids']:
                obj = self.cache.get(object_type, _id)
                if not obj:
                    return self._get(self._build_url(endpoint=endpoint(*endpoint_args, **endpoint_kwargs)))
                cached_objects.append(obj)
            return ZendeskResultGenerator(self, {}, response_objects=cached_objects, object_type=object_type)
        else:
            return self._get(self._build_url(endpoint=endpoint(*endpoint_args, **endpoint_kwargs)))

    def _check_response(self, response):
        """
        Check the response code returned by Zendesk. If it is outside the 200 range, raise an exception of the correct type.

        :param response: requests Response object.
        """
        if response.status_code > 299 or response.status_code < 200:
            log.debug("Received response code [%s] - headers: %s" % (response.status_code, str(response.headers)))
            try:
                _json = response.json()
                err_type = _json.get("error", '')
                if err_type == 'RecordNotFound':
                    raise RecordNotFoundException(json.dumps(_json), response=response)
                elif err_type == "TooManyValues":
                    raise TooManyValuesException(json.dumps(_json), response=response)
                else:
                    raise APIException(json.dumps(_json), response=response)
            except ValueError:
                response.raise_for_status()

    def _build_url(self, endpoint):
        """ Build complete URL """
        if not issubclass(type(self), ChatApiBase) and not self.subdomain:
            raise ZenpyException("subdomain is required when accessing the Zendesk API!")

        if self.subdomain:
            endpoint.netloc = '{}.{}'.format(self.subdomain, self.domain)
        else:
            endpoint.netloc = self.domain

        endpoint.prefix_path(self.api_prefix)
        return endpoint.build()


class Api(BaseApi):
    """
    Most general API class. It is callable, and is suitable for basic API endpoints.

    This class also contains many methods for retrieving specific objects or collections of objects.
    These methods are called by the classes found in zenpy.lib.api_objects.
    """

    def __init__(self, config, object_type, endpoint=None):
        self.object_type = object_type
        self.endpoint = endpoint or EndpointFactory(as_plural(object_type))
        super(Api, self).__init__(**config)
        self._object_mapping = ZendeskObjectMapping(self)

    def __call__(self, *args, **kwargs):
        return self._query_zendesk(self.endpoint, self.object_type, *args, **kwargs)

    def _get_user(self, user_id):
        return self._query_zendesk(EndpointFactory('users'), 'user', id=user_id)

    def _get_users(self, user_ids):
        return self._query_zendesk(endpoint=EndpointFactory('users'), object_type='user', ids=user_ids)

    def _get_comment(self, comment_id):
        return self._query_zendesk(endpoint=EndpointFactory('tickets').comments, object_type='comment', id=comment_id)

    def _get_organization(self, organization_id):
        return self._query_zendesk(endpoint=EndpointFactory('organizations'), object_type='organization',
                                   id=organization_id)

    def _get_group(self, group_id):
        return self._query_zendesk(endpoint=EndpointFactory('groups'), object_type='group', id=group_id)

    def _get_brand(self, brand_id):
        return self._query_zendesk(endpoint=EndpointFactory('brands'), object_type='brand', id=brand_id)

    def _get_ticket(self, ticket_id):
        return self._query_zendesk(endpoint=EndpointFactory('tickets'), object_type='ticket', id=ticket_id)

    def _get_sharing_agreements(self, sharing_agreement_ids):
        sharing_agreements = []
        for _id in sharing_agreement_ids:
            sharing_agreement = self._query_zendesk(endpoint=EndpointFactory('sharing_agreements'),
                                                    object_type='sharing_agreement',
                                                    id=_id)
            if sharing_agreement:
                sharing_agreements.append(sharing_agreement)
        return sharing_agreements

    def _get_problem(self, problem_id):
        return self._query_zendesk(EndpointFactory('tickets'), 'ticket', id=problem_id)

    # This will be deprecated soon - https://developer.zendesk.com/rest_api/docs/web-portal/forums
    def _get_forum(self, forum_id):
        return forum_id

    def _get_restricted_brands(self, brand_ids):
        for brand_id in brand_ids:
            yield self._query_zendesk(EndpointFactory('brands'), 'brand', id=brand_id)

    def _get_restricted_organizations(self, organization_ids):
        for org_id in organization_ids:
            yield self._query_zendesk(EndpointFactory("organizations"), 'organization', id=org_id)

    def _get_ticket_fields(self, ticket_field_ids):
        for field_id in ticket_field_ids:
            yield self._query_zendesk(EndpointFactory('ticket_fields'), 'ticket_field', id=field_id)

    def _get_view(self, view_id):
        return self._query_zendesk(EndpointFactory('views'), 'view', id=view_id)

    def _get_topic(self, forum_topic_id):
        return self._query_zendesk(EndpointFactory('help_centre').topics, 'topic', id=forum_topic_id)

    def _get_category(self, category_id):
        return self._query_zendesk(EndpointFactory('help_centre').categories, 'category', id=category_id)

    def _get_macro(self, macro_id):
        return self._query_zendesk(EndpointFactory('macros'), 'macro', id=macro_id)

    def _get_sla(self, sla_id):
        return self._query_zendesk(EndpointFactory('sla_policies'), 'sla_policy', id=sla_id)

    def _get_department(self, department_id):
        return self._query_zendesk(EndpointFactory('chats').departments, 'department', id=department_id)

    def _get_zendesk_ticket(self, ticket_id):
        return self._query_zendesk(EndpointFactory('tickets'), 'ticket', id=ticket_id)

    def _get_user_segment(self, user_segment_id):
        return self._query_zendesk(EndpointFactory('help_centre').user_segments, 'segment', id=user_segment_id)

    def _get_section(self, section_id):
        return self._query_zendesk(EndpointFactory('help_centre').sections, 'section', id=section_id)

    def _get_article(self, article_id):
        return self._query_zendesk(EndpointFactory('help_centre').articles, 'article', id=article_id)

    def _get_custom_role(self, custom_role_id):
        return self._query_zendesk(EndpointFactory('custom_agent_roles'), 'custom_role', id=custom_role_id)

    # TODO: Implement these methods when the NPS API is done
    def _get_delivery(self, delivery_id):
        pass

    def _get_survey(self, survery_id):
        pass

    def _get_default_locale(self, locale_id):
        return self._query_zendesk(EndpointFactory('locales'), 'locale', id=locale_id)

class CRUDApi(Api):
    """
    CRUDApi supports create/update/delete operations
    """

    def create(self, api_objects, **kwargs):
        """
        Create (POST) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param api_objects: object or objects to create
        """
        return CRUDRequest(self).post(api_objects)

    def update(self, api_objects, **kwargs):
        """
        Update (PUT) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param api_objects: object or objects to update
        """
        return CRUDRequest(self).put(api_objects)

    def delete(self, api_objects, **kwargs):
        """
        Delete (DELETE) one or more API objects. After successfully deleting the objects from the API
        they will also be removed from the relevant Zenpy caches.

        :param api_objects: object or objects to delete
        """

        return CRUDRequest(self).delete(api_objects)


class CRUDExternalApi(CRUDApi):
    """
    The CRUDExternalApi exposes some extra methods for operating on external ids.
    """

    def update_by_external_id(self, api_objects):
        """
        Update (PUT) one or more API objects by external_id.

        :param api_objects:
        """
        if not isinstance(api_objects, Iterable):
            api_objects = [api_objects]
        return CRUDRequest(self).put(api_objects, update_many_external=True)

    def delete_by_external_id(self, api_objects):
        """
        Delete (DELETE) one or more API objects by external_id.

        :param api_objects:
        """
        if not isinstance(api_objects, Iterable):
            api_objects = [api_objects]
        return CRUDRequest(self).delete(api_objects, destroy_many_external=True)


class SuspendedTicketApi(Api):
    """
    The SuspendedTicketApi adds some SuspendedTicket specific functionality
    """

    def recover(self, tickets):
        """
        Recover (PUT) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to recover
        """
        return SuspendedTicketRequest(self).put(tickets)

    def delete(self, tickets):
        """
        Delete (DELETE) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to delete
        """
        return SuspendedTicketRequest(self).delete(tickets)


class TaggableApi(Api):
    """
    TaggableApi supports getting, setting, adding and deleting tags.
    """

    def add_tags(self, id, tags):
        """
        Add (PUT) one or more tags.

        :param id: the id of the object to tag
        :param tags: array of tags to apply to object
        """
        return TagRequest(self).put(tags, id)

    def set_tags(self, id, tags):
        """
        Set (POST) one or more tags.

        :param id: the id of the object to tag
        :param tags: array of tags to apply to object
        """
        return TagRequest(self).post(tags, id)

    def delete_tags(self, id, tags):
        """
        Delete (DELETE) one or more tags.

        :param id: the id of the object to delete tag from
        :param tags: array of tags to delete from object
        """
        return TagRequest(self).delete(tags, id)

    def tags(self, ticket_id):
        """
        Lists the most popular recent tags in decreasing popularity from a specific ticket.
        """
        return self._query_zendesk(self.endpoint.tags, 'tag', id=ticket_id)


# noinspection PyShadowingBuiltins
class RateableApi(Api):
    """
    Supports rating with a SatisfactionRating
    """

    def rate(self, id, rating):
        """
        Add (POST) a satisfaction rating.

        :param id: id of object to rate
        :param rating: SatisfactionRating
        """
        return RateRequest(self).post(rating, id)


class IncrementalApi(Api):
    """
    IncrementalApi supports the incremental endpoint.
    """

    def incremental(self, start_time, include=None):
        """
        Retrieve bulk data from the incremental API.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param start_time: The time of the oldest object you are interested in.
        """
        return self._query_zendesk(self.endpoint.incremental, self.object_type, start_time=start_time, include=include)


class ChatIncrementalApi(Api):
    """
    ChatIncrementalApi supports the chat incremental endpoint.
    """

    def incremental(self, start_time, **kwargs):
        """
        Retrieve bulk data from the chat incremental API.

        :param fields: list of fields to retrieve. `Chat API Docs
            <https://developer.zendesk.com/rest_api/docs/chat/incremental_export#usage-notes-resource-expansion>`__.
        :param start_time: The time of the oldest object you are interested in.
        """
        return self._query_zendesk(self.endpoint.incremental, self.object_type, start_time=start_time, **kwargs)

class UserIdentityApi(Api):
    def __init__(self, config):
        super(UserIdentityApi, self).__init__(config,
                                              object_type='identity',
                                              endpoint=EndpointFactory('users').identities)

    @extract_id(User, Identity)
    def show(self, user, identity):
        """
        Show the specified identity for the specified user.

        :param user: user id or User object
        :param identity: identity id object
        :return: Identity
        """
        url = self._build_url(self.endpoint.show(user, identity))
        return self._get(url)

    @extract_id(User)
    def create(self, user, identity):
        """
        Create an additional identity for the specified user

        :param user: User id or object
        :param identity: Identity object to be created
        """
        return UserIdentityRequest(self).post(user, identity)

    @extract_id(User, Identity)
    def update(self, user, identity):
        """
        Update specified identity for the specified user

        :param user: User object or id
        :param identity: Identity object to be updated.
        :return: The updated Identity
        """
        return UserIdentityRequest(self).put(self.endpoint.update, user, identity)

    @extract_id(User, Identity)
    def make_primary(self, user, identity):
        """
        Set the specified user as primary for the specified user.

        :param user: User object or id
        :param identity: Identity object or id
        :return: list of user's Identities
        """
        return UserIdentityRequest(self).put(self.endpoint.make_primary, user, identity)

    @extract_id(User, Identity)
    def request_verification(self, user, identity):
        """
        Sends the user a verification email with a link to verify ownership of the email address.

        :param user: User id or object
        :param identity: Identity id or object
        :return: requests Response object
        """
        return UserIdentityRequest(self).put(self.endpoint.request_verification, user, identity)

    @extract_id(User, Identity)
    def verify(self, user, identity):
        """
        Verify an identity for a user

        :param user: User id or object
        :param identity: Identity id or object
        :return: the verified Identity
        """
        return UserIdentityRequest(self).put(self.endpoint.verify, user, identity)

    @extract_id(User, Identity)
    def delete(self, user, identity):
        """
        Deletes the identity for a given user

        :param user: User id or object
        :param identity: Identity id or object
        :return: requests Response object
        """
        return UserIdentityRequest(self).delete(user, identity)


class UserApi(IncrementalApi, CRUDExternalApi, TaggableApi):
    """
    The UserApi adds some User specific functionality
    """

    def __init__(self, config):
        super(UserApi, self).__init__(config, object_type='user')
        self.identities = UserIdentityApi(config)

    @extract_id(User)
    def groups(self, user, include=None):
        """
        Retrieve the groups for this user.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param user: User object or id
        """
        return self._query_zendesk(self.endpoint.groups, 'group', id=user, include=include)

    @extract_id(User)
    def organizations(self, user, include=None):
        """
        Retrieve the organizations for this user.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param user: User object or id
        """
        return self._query_zendesk(self.endpoint.organizations, 'organization', id=user, include=include)

    @extract_id(User)
    def requested(self, user, include=None):
        """
        Retrieve the requested tickets for this user.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param user: User object or id
        """
        return self._query_zendesk(self.endpoint.requested, 'ticket', id=user, include=include)

    @extract_id(User)
    def cced(self, user, include=None):
        """
        Retrieve the tickets this user is cc'd into.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param user: User object or id
        """
        return self._query_zendesk(self.endpoint.cced, 'ticket', id=user, include=include)

    @extract_id(User)
    def assigned(self, user, include=None):
        """
        Retrieve the assigned tickets for this user.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param user: User object or id
        """
        return self._query_zendesk(self.endpoint.assigned, 'ticket', id=user, include=include)

    @extract_id(User)
    def group_memberships(self, user, include=None):
        """
        Retrieve the group memberships for this user.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param user: User object or id
        """
        return self._query_zendesk(self.endpoint.group_memberships, 'group_membership', id=user, include=include)

    def requests(self, **kwargs):
        return self._query_zendesk(self.endpoint.requests, 'request', **kwargs)

    @extract_id(User)
    def related(self, user):
        """
        Returns the UserRelated information for the requested User

        :param user: User object or id
        :return: UserRelated
        """
        return self._query_zendesk(self.endpoint.related, 'user_related', id=user)

    def me(self, include=None):
        """
        Return the logged in user

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading#abilities>`__.
        """
        return self._query_zendesk(self.endpoint.me, 'user', include=include)

    @extract_id(User)
    def merge(self, source_user, dest_user):
        """
        Merge the user provided in source_user into dest_user

        :param source_user: User object or id of user to be merged
        :param dest_user: User object or id to merge into
        :return: The merged User
        """
        return UserMergeRequest(self).put(source_user, dest_user)

    @extract_id(User)
    def user_fields(self, user):
        """
        Retrieve the user fields for this user.

        :param user: User object or id
        """
        return self._query_zendesk(self.endpoint.user_fields, 'user_field', id=user)

    @extract_id(User)
    def organization_memberships(self, user):
        """
        Retrieve the organization memberships for this user.

        :param user: User object or id
        """
        return self._query_zendesk(self.endpoint.organization_memberships, 'organization_membership', id=user)

    def create_or_update(self, users):
        """
        Creates a user (POST) if the user does not already exist, or updates an existing user identified
        by e-mail address or external ID.

        :param users: User object or list of User objects
        :return: the created/updated User or a  JobStatus object if a list was passed
        """

        return CRUDRequest(self).post(users, create_or_update=True)

    @extract_id(User)
    def permanently_delete(self, user):
        """
        Permanently delete user. User should be softly deleted first.
        Zendesk API `Reference <https://developer.zendesk.com/rest_api/docs/core/users#permanently-delete-user>`__.

        Note: This endpoint does not support multiple ids or list of `User` objects.

        :param user: User object or id.
        :return: User object with `permanently_deleted` status
        """
        url = self._build_url(self.endpoint.deleted(id=user))
        deleted_user = self._delete(url)
        self.cache.delete(deleted_user)
        return deleted_user

    def deleted(self):
        """
        List Deleted Users.

        These are users that have been deleted but not permanently yet.
        Zendesk API `Reference <https://developer.zendesk.com/rest_api/docs/core/users#permanently-delete-user>`__.

        :return:
        """
        return self._get(self._build_url(self.endpoint.deleted()))

    @extract_id(User)
    def skips(self, user):
        """
        Skips for user. Zendesk API `Reference <https://developer.zendesk.com/rest_api/docs/core/ticket_skips>`__.
        """
        return self._get(self._build_url(self.endpoint.skips(id=user)))

    @extract_id(User)
    def set_password(self, user, password):
        """
        Sets the password for the passed user.
        Zendesk API `Reference <https://developer.zendesk.com/rest_api/docs/support/users#set-a-users-password>`__.

        :param user: User object or id
        :param password: new password
        """
        url = self._build_url(self.endpoint.set_password(id=user))
        return self._post(url, payload=dict(password=password))


class AttachmentApi(Api):
    def __init__(self, config):
        super(AttachmentApi, self).__init__(config, object_type='attachment')

    def __call__(self, *args, **kwargs):
        if 'id' not in kwargs:
            raise ZenpyException("Attachment endpoint requires an id")
        return Api.__call__(self, **kwargs)

    def upload(self, fp, token=None, target_name=None, content_type=None):
        """
        Upload a file to Zendesk.

        :param fp: file object, StringIO instance, content, or file path to be
                   uploaded
        :param token: upload token for uploading multiple files
        :param target_name: name of the file inside Zendesk
        :return: :class:`Upload` object containing a token and other information see
            Zendesk API `Reference <https://developer.zendesk.com/rest_api/docs/core/attachments#uploading-files>`__.
        """
        return UploadRequest(self).post(fp, token=token, target_name=target_name, content_type=content_type)

    def download(self, attachment_id, destination):
        """
        Download an attachment from Zendesk.

        :param attachment_id: id of the attachment to download
        :param destination: destination path. If a directory, the file will be placed in the directory with
                            the filename from the Attachment object.
        :return: the path the file was written to
        """
        attachment = self(id=attachment_id)
        if os.path.isdir(destination):
            destination = os.path.join(destination, attachment.file_name)
        return self._download_file(attachment.content_url, destination)

    def _download_file(self, source_url, destination_path):
        r = self.session.get(source_url, stream=True)
        with open(destination_path, 'wb') as f:
            # chunk_size of None will read data as it arrives in whatever size the chunks are received.
            for chunk in r.iter_content(chunk_size=None):
                if chunk:
                    f.write(chunk)
        return destination_path


class EndUserApi(CRUDApi):
    """
    EndUsers can only update.
    """

    def __init__(self, config):
        super(EndUserApi, self).__init__(config, object_type='user', endpoint=EndpointFactory('end_user'))

    def __call__(self, *args, **kwargs):
        raise ZenpyException("EndUserApi is not callable!")

    @extract_id(User)
    def show(self, user):
        return self._query_zendesk(self.endpoint, object_type='user', id=user)

    def delete(self, api_objects, **kwargs):
        raise ZenpyException("EndUsers cannot delete!")

    def create(self, api_objects, **kwargs):
        raise ZenpyException("EndUsers cannot create!")


class OrganizationApi(TaggableApi, IncrementalApi, CRUDExternalApi):
    def __init__(self, config):
        super(OrganizationApi, self).__init__(config, object_type='organization')

    @extract_id(Organization)
    def users(self, organization, include=None):
        return self._get(self._build_url(self.endpoint.users(id=organization, include=include)))

    @extract_id(Organization)
    def organization_fields(self, organization):
        """
        Retrieve the organization fields for this organization.

        :param organization: Organization object or id
        """
        return self._query_zendesk(self.endpoint.organization_fields, 'organization_field', id=organization)

    @extract_id(Organization)
    def organization_memberships(self, organization):
        """
        Retrieve tche organization fields for this organization.

        :param organization: Organization object or id
        """
        return self._query_zendesk(self.endpoint.organization_memberships, 'organization_membership', id=organization)

    def external(self, external_id, include=None):
        """
        Locate an Organization by it's external_id attribute.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param external_id: external id of organization
        """
        return self._query_zendesk(self.endpoint.external, 'organization', id=external_id, include=include)

    def requests(self, **kwargs):
        return self._query_zendesk(self.endpoint.requests, 'request', **kwargs)

    def create_or_update(self, organization):
        """
        Creates an organization if it doesn't already exist, or updates an existing
        organization identified by ID or external ID

        :param organization: Organization object
        :return: the created/updated Organization
        """

        return CRUDRequest(self).post(organization, create_or_update=True)


class OrganizationMembershipApi(CRUDApi):
    """
    The OrganizationMembershipApi allows the creation and deletion of Organization Memberships
    """

    def __init__(self, config):
        super(OrganizationMembershipApi, self).__init__(config, object_type='organization_membership')

    def update(self, items, **kwargs):
        raise ZenpyException("You cannot update Organization Memberships!")


class OrganizationFieldsApi(CRUDApi):
    def __init__(self, config):
        super(OrganizationFieldsApi, self).__init__(config, object_type='organization_field')

    @extract_id(OrganizationField)
    def reorder(self, organization_fields):
        """
        Reorder organization fields.

        :param organization_fields: list of OrganizationField objects or ids in the desired order.
        """
        return OrganizationFieldReorderRequest(self).put(organization_fields)


class SatisfactionRatingApi(Api):
    def __init__(self, config):
        super(SatisfactionRatingApi, self).__init__(config, object_type='satisfaction_rating')

    @extract_id(Ticket)
    def create(self, ticket, satisfaction_rating):
        """
        Create/update a Satisfaction Rating for a ticket.

        :param ticket: Ticket object or id
        :param satisfaction_rating: SatisfactionRating object.
        """
        return SatisfactionRatingRequest(self).post(ticket, satisfaction_rating)


class MacroApi(CRUDApi):
    def __init__(self, config):
        super(MacroApi, self).__init__(config, object_type='macro')

    @extract_id(Macro)
    def apply(self, macro):
        """
        Show what a macro would do
        Zendesk API `Reference <https://developer.zendesk.com/rest_api/docs/core/macros#show-changes-to-ticket>`__.

        :param macro: Macro object or id.
        """

        return self._query_zendesk(self.endpoint.apply, 'result', id=macro)


class TicketApi(RateableApi, TaggableApi, IncrementalApi, CRUDApi):
    """
    The TicketApi adds some Ticket specific functionality
    """

    def __init__(self, config):
        super(TicketApi, self).__init__(config, object_type='ticket')

    @extract_id(Organization)
    def organizations(self, organization, include=None):
        """
        Retrieve the tickets for this organization.

        :param include: list of objects to sideload. `Side-loading API Docs
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param organization: Organization object or id
        """
        return self._query_zendesk(self.endpoint.organizations, 'ticket', id=organization, include=include)

    def recent(self, include=None):
        """
        Retrieve the most recent tickets
        """
        return self._query_zendesk(self.endpoint.recent, 'ticket', id=None, include=include)

    @extract_id(Ticket)
    def comments(self, ticket, include_inline_images=False):
        """
        Retrieve the comments for a ticket.

        :param ticket: Ticket object or id
        :param include_inline_images: Boolean. If `True`, inline image attachments will be
            returned in each comments' `attachments` field alongside non-inline attachments
        """
        return self._query_zendesk(self.endpoint.comments, 'comment', id=ticket, include_inline_images=repr(include_inline_images).lower())

    @extract_id(Ticket, TicketComment)
    def comment_redact(self, ticket, comment, text):
        """
        Redact text from ticket comment. `See Zendesk API docs <https://developer.zendesk.com/rest_api/docs/support/ticket_comments#redact-string-in-comment>`_

        :param ticket: Ticket object or id
        :param comment: Comment object or id
        :param text: Text to be redacted from comment
        :return Comment: Ticket Comment object
        """

        return self._put(self._build_url(self.endpoint.comments.redact(ticket, comment)), {'text': text})

    def permanently_delete(self, tickets):
        """
        Permanently delete ticket. `See Zendesk API docs <https://developer.zendesk.com/rest_api/docs/support/tickets#delete-ticket-permanently>`_

        Ticket should be softly deleted first with regular `delete` method.

        :param tickets: Ticket object or list of tickets objects
        :return: JobStatus object
        """
        endpoint_kwargs = dict()
        if isinstance(tickets, Iterable):
            endpoint_kwargs['destroy_ids'] = [i.id for i in tickets]
        else:
            endpoint_kwargs['id'] = tickets.id
        url = self._build_url(self.endpoint.deleted(**endpoint_kwargs))
        deleted_ticket_job_id = self._delete(url)
        self.cache.delete(tickets)
        return deleted_ticket_job_id

    def deleted(self):
        """
        List Deleted Tickets.

        These are tickets that have been deleted but not permanently yet.
        See Permanently delete ticket in `Zendesk API docs <https://developer.zendesk.com/rest_api/docs/support/tickets#delete-ticket-permanently>`_

        :return: ResultGenerator with Tickets objects with length 0 of no deleted tickets exist.
        """
        return self._get(self._build_url(self.endpoint.deleted()))

    def events(self, start_time, include=None):
        """
        Retrieve TicketEvents

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param start_time: time to retrieve events from.
        """
        return self._query_zendesk(self.endpoint.events, 'ticket_event', start_time=start_time, include=include)

    @extract_id(Ticket)
    def audits(self, ticket=None, include=None, **kwargs):
        """
        Retrieve TicketAudits. If ticket is passed, return the tickets for a specific audit.

        If ticket_id is None, a TicketAuditGenerator is returned to handle pagination. The way this generator
        works is a different to the other Zenpy generators as it is cursor based, allowing you to change the
        direction that you are consuming objects. This is done with the reversed() python method.

        For example:

        .. code-block:: python

            for audit in reversed(zenpy_client.tickets.audits()):
                print(audit)

        See the `Zendesk docs <https://developer.zendesk.com/rest_api/docs/core/ticket_audits#pagination>`__ for
        information on additional parameters.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param ticket: Ticket object or id
        """
        if ticket is not None:
            return self._query_zendesk(self.endpoint.audits, 'ticket_audit', id=ticket, include=include)
        else:
            return self._query_zendesk(self.endpoint.audits.cursor, 'ticket_audit', include=include, **kwargs)

    @extract_id(Ticket)
    def metrics(self, ticket):
        """
        Retrieve TicketMetric.

        :param ticket: Ticket object or id
        """
        return self._query_zendesk(self.endpoint.metrics, 'ticket_metric', id=ticket)

    def metrics_incremental(self, start_time):
        """
        Retrieve TicketMetric incremental

        :param start_time: time to retrieve events from.
        """
        return self._query_zendesk(self.endpoint.metrics.incremental, 'ticket_metric_events', start_time=start_time)

    @extract_id(Ticket, Macro)
    def show_macro_effect(self, ticket, macro):
        """
        Apply macro to ticket. Returns what it *would* do, does not alter the ticket.

        :param ticket: Ticket or ticket id to target
        :param macro: Macro or macro id to use
        """

        url = self._build_url(self.endpoint.macro(ticket, macro))
        macro_effect = self._get(url)
        macro_effect._set_dirty()
        return macro_effect

    @extract_id(Ticket)
    def merge(self, target, source,
              target_comment=None, source_comment=None):
        """
        Merge the ticket(s) or ticket ID(s) in source into the target ticket.

        :param target: ticket id or object to merge tickets into
        :param source: ticket id, object or list of tickets or ids to merge into target
        :param source_comment: optional comment for the source ticket(s)
        :param target_comment: optional comment for the target ticket

        :return: a JobStatus object
        """
        return TicketMergeRequest(self).post(target, source,
                                             target_comment=target_comment,
                                             source_comment=source_comment)

    @extract_id(Ticket)
    def skips(self, ticket):
        """
        Skips for ticket See Zendesk API `Reference <https://developer.zendesk.com/rest_api/docs/core/ticket_skips>`__.
        """

        return self._get(self._build_url(self.endpoint.skips(id=ticket)))


class SkipApi(CRUDApi):
    def __init__(self, config):
        super(SkipApi, self).__init__(config,
                                      object_type='skip',
                                      endpoint=EndpointFactory('skips'))

    def delete(self, api_objects, **kwargs):
        raise NotImplementedError("Cannot delete Skip objects")

    def update(self, api_objects, **kwargs):
        raise NotImplementedError("Cannot update Skip objects")


class TicketImportAPI(CRUDApi):
    def __init__(self, config):
        super(TicketImportAPI, self).__init__(config,
                                              object_type='ticket',
                                              endpoint=EndpointFactory('ticket_import'))

    def __call__(self, *args, **kwargs):
        raise ZenpyException("This endpoint cannot be called directly!")

    def update(self, items, **kwargs):
        raise ZenpyException("You cannot update objects using ticket_import endpoint!")

    def delete(self, api_objects, **kwargs):
        raise ZenpyException("You cannot delete objects using the ticket_import endpoint!")


class TicketCustomFieldOptionApi(Api):

    def __init__(self, config):
        super(TicketCustomFieldOptionApi, self).__init__(config,
                                                         object_type='custom_field_option',
                                                         endpoint=EndpointFactory('ticket_field_options'))

    @extract_id(TicketField, CustomFieldOption)
    def show(self, ticket_field, custom_field_option):
        """
        Return CustomFieldOption

        :param ticket_field: TicketFieldOption or id
        :param custom_field_option: CustomFieldOption or id
        """
        return self._query_zendesk(self.endpoint.show, 'custom_field_option', ticket_field, custom_field_option)

    @extract_id(TicketField)
    def create_or_update(self, ticket_field, custom_field_option):
        """
        Create or update a CustomFieldOption for a TicketField. If passed CustomFieldOption has no id, a new option
        will be created, otherwise it is updated - See: Zendesk API `Reference
        <https://developer.zendesk.com/rest_api/docs/core/ticket_fields#create-or-update-a-ticket-field-option>`__.

        :param ticket_field: TicketField object or id
        :param custom_field_option: CustomFieldOption object
        """
        return TicketFieldOptionRequest(self).post(ticket_field, custom_field_option)

    @extract_id(TicketField, CustomFieldOption)
    def delete(self, ticket_field, custom_field_option):
        """
        Delete a CustomFieldOption.

        :param ticket_field: TicketField object or id.
        :param custom_field_option: CustomFieldOption
        """
        return TicketFieldOptionRequest(self).delete(ticket_field, custom_field_option)


class TicketFieldApi(CRUDApi):

    def __init__(self, config):
        super(TicketFieldApi, self).__init__(config, 'ticket_field')
        self.options = TicketCustomFieldOptionApi(config)


class VariantApi(Api):
    def __init__(self, config, endpoint):
        super(VariantApi, self).__init__(config,
                                         object_type='variant',
                                         endpoint=endpoint)

    @extract_id(Item, Variant)
    def show(self, item, variant):
        """
        Show a variant.

        :param item: Item object or id
        :param variant: Variant object or id
        :return:
        """
        url = self._build_url(self.endpoint.show(item, variant))
        return self._get(url)

    @extract_id(Item)
    def create(self, item, variant):
        """
        Create one or more variants.

        :param item: Item object or id
        :param variant: Variant object or list of objects
        """
        return VariantRequest(self).post(item, variant)

    @extract_id(Item)
    def update(self, item, variant):
        """
        Update one or more variants.

        :param item: Item object or id
        :param variant: Variant object or list of objects
        """
        return VariantRequest(self).put(item, variant)

    @extract_id(Item, Variant)
    def delete(self, item, variant):
        """
        Delete a variant.

        :param item: Item object or id
        :param variant: Variant object or id
        """
        return VariantRequest(self).delete(item, variant)


class DynamicContentApi(CRUDApi):
    def __init__(self, config):
        super(DynamicContentApi, self).__init__(config,
                                                object_type='item',
                                                endpoint=EndpointFactory('dynamic_contents'))
        self.variants = VariantApi(config, endpoint=self.endpoint.variants)


class TriggerApi(CRUDApi):
    pass


class AutomationApi(CRUDApi):
    pass


class TargetApi(CRUDApi):
    pass


class BrandApi(CRUDApi):
    pass


class TicketFormApi(CRUDApi):
    pass


class RequestAPI(CRUDApi):
    def __init__(self, config):
        super(RequestAPI, self).__init__(config, object_type='request')

    def open(self):
        """
        Return all open requests
        """
        return self._query_zendesk(self.endpoint.open, 'request')

    def solved(self):
        """
        Return all solved requests
        """
        return self._query_zendesk(self.endpoint.solved, 'request')

    def ccd(self):
        """
        Return all ccd requests
        """
        return self._query_zendesk(self.endpoint.ccd, 'request')

    def comments(self, request_id):
        """
        Return comments for request
        """
        return self._query_zendesk(self.endpoint.comments, 'comment', id=request_id)

    def delete(self, api_objects, **kwargs):
        raise ZenpyException("You cannot delete requests!")

    def search(self, *args, **kwargs):
        """
        Search for requests. See the `Zendesk docs
        <https://developer.zendesk.com/rest_api/docs/core/requests#searching-requests>`__ for more information on the
        syntax.
        """
        return self._query_zendesk(self.endpoint.search, 'request', *args, **kwargs)


class SharingAgreementAPI(CRUDApi):
    def __init__(self, config):
        super(SharingAgreementAPI, self).__init__(config, object_type='sharing_agreement')


class GroupApi(CRUDApi):
    def __init__(self, config):
        super(GroupApi, self).__init__(config, object_type='group')

    @extract_id(Group)
    def users(self, group, include=None):
        return self._get(self._build_url(self.endpoint.users(id=group, include=include)))

    @extract_id(Group)
    def memberships(self, group, include=None):
        """
        Return the GroupMemberships for this group.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param group: Group object or id
        """
        return self._get(self._build_url(self.endpoint.memberships(id=group, include=include)))

    @extract_id(Group)
    def memberships_assignable(self, group, include=None):
        """
        Return memberships that are assignable for this group.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param group: Group object or id
        """
        return self._get(self._build_url(self.endpoint.memberships_assignable(id=group, include=include)))


class ViewApi(CRUDApi):
    def __init__(self, config):
        super(ViewApi, self).__init__(config, object_type='view')

    def active(self, include=None):
        """
        Return all active views.
        """
        return self._get(self._build_url(self.endpoint.active(include=include)))

    def compact(self, include=None):
        """
        Return compact views - See: Zendesk API `Reference
        <https://developer.zendesk.com/rest_api/docs/core/views#list-views---compact>`__
        """
        return self._get(self._build_url(self.endpoint.compact(include=include)))

    @extract_id(View)
    def execute(self, view, include=None):
        """
        Execute a view.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param view: View or view id
        """
        return self._get(self._build_url(self.endpoint.execute(id=view, include=include)))

    @extract_id(View)
    def tickets(self, view, include=None):
        """
        Return the tickets in a view.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param view: View or view id
        """
        return self._get(self._build_url(self.endpoint.tickets(id=view, include=include)))

    @extract_id(View)
    def count(self, view, include=None):
        """
        Return a ViewCount for a view.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param view: View or view id
        """
        return self._get(self._build_url(self.endpoint.count(id=view, include=include)))

    @extract_id(View)
    def count_many(self, views, include=None):
        """
        Return many ViewCounts.

        :param include: list of objects to sideload. `Side-loading API Docs 
            <https://developer.zendesk.com/rest_api/docs/core/side_loading>`__.
        :param views: iterable of View or view ids
        """
        return self._get(self._build_url(self.endpoint(count_many=views, include=include)))

    @extract_id(View)
    def export(self, view, include=None):
        """
        Export a view. Returns an Export object.

        :param include: list of objects to sideload. `Side-loading API Docs 

        :param view: View or view id
        :return:
        """
        return self._get(self._build_url(self.endpoint.export(id=view, include=include)))

    def search(self, *args, **kwargs):
        """
        Search views. See Zendesk API `Reference <https://developer.zendesk.com/rest_api/docs/core/views#search-views>`__.

        :param args: query is the only accepted arg.
        :param kwargs: search parameters
        """
        return self._get(self._build_url(self.endpoint.search(*args, **kwargs)))

    # TODO: https://github.com/facetoe/zenpy/issues/123
    def _get_sla(self, sla_id):
        pass


class GroupMembershipApi(CRUDApi):
    def __init__(self, config):
        super(GroupMembershipApi, self).__init__(config, object_type='group_membership')

    def update(self, api_objects, **kwargs):
        raise ZenpyException("Cannot update GroupMemberships")

    def assignable(self):
        """
        Return GroupMemberships that are assignable.
        """
        return self._get(self._build_url(self.endpoint.assignable()))

    @extract_id(User, GroupMembership)
    def make_default(self, user, group_membership):
        """
        Set the passed GroupMembership as default for the specified user.

        :param user: User object or id
        :param group_membership: GroupMembership object or id
        """
        return self._put(self._build_url(self.endpoint.make_default(user, group_membership)), payload={})


class JiraLinkApi(CRUDApi):
    def __init__(self, config):
        super(JiraLinkApi, self).__init__(config, object_type='link')
        self.api_prefix = "api"

    def update(self, api_objects, **kwargs):
        raise ZenpyException("Cannot update Jira Links!")


class SlaPolicyApi(CRUDApi):
    def __init__(self, config):
        super(SlaPolicyApi, self).__init__(config, object_type='sla_policy')

    def create(self, api_objects, **kwargs):
        if isinstance(api_objects, Iterable):
            raise ZenpyException("Cannot create multiple sla policies!")
        super(SlaPolicyApi, self).create(api_objects, **kwargs)

    def update(self, api_objects, **kwargs):
        if isinstance(api_objects, Iterable):
            raise ZenpyException("Cannot update multiple sla policies!")
        super(SlaPolicyApi, self).update(api_objects, **kwargs)

    def definitions(self):
        url = self._build_url(self.endpoint.definitions())
        return self._get(url)


class RecipientAddressApi(CRUDApi):
    def __init__(self, config):
        super(RecipientAddressApi, self).__init__(config, object_type='recipient_address')


class ChatApiBase(Api):
    """
    Implements most generic ChatApi functionality. Most if the actual work is delegated to
    Request and Response handlers.
    """

    def __init__(self, config, endpoint, request_handler=None):
        super(ChatApiBase, self).__init__(config,
                                          object_type='chat',
                                          endpoint=endpoint)
        self.domain = 'www.zopim.com'
        self.subdomain = ''
        self._request_handler = request_handler or ChatApiRequest
        self._object_mapping = ChatObjectMapping(self)
        self._response_handlers = (
            DeleteResponseHandler,
            ChatSearchResponseHandler,
            ChatResponseHandler,
            AccountResponseHandler,
            AgentResponseHandler,
            VisitorResponseHandler,
            ShortcutResponseHandler,
            TriggerResponseHandler,
            BanResponseHandler,
            DepartmentResponseHandler,
            GoalResponseHandler
        )

    def create(self, *args, **kwargs):
        return self._request_handler(self).post(*args, **kwargs)

    def update(self, *args, **kwargs):
        return self._request_handler(self).put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request_handler(self).delete(*args, **kwargs)

    def _get_ip_address(self, ips):
        for ip in ips:
            yield self._object_mapping.object_from_json('ip_address', ip)


class AgentApi(ChatApiBase):
    def __init__(self, config, endpoint):
        super(AgentApi, self).__init__(config,
                                       endpoint=endpoint,
                                       request_handler=AgentRequest)

    def me(self):
        return self._get(self._build_url(self.endpoint.me()))


class ChatApi(ChatApiBase, ChatIncrementalApi):
    def __init__(self, config, endpoint):
        super(ChatApi, self).__init__(config, endpoint=endpoint)

        self.accounts = ChatApiBase(config, endpoint.account, request_handler=AccountRequest)
        self.agents = AgentApi(config, endpoint.agents)
        self.visitors = ChatApiBase(config, endpoint.visitors, request_handler=VisitorRequest)
        self.shortcuts = ChatApiBase(config, endpoint.shortcuts)
        self.triggers = ChatApiBase(config, endpoint.triggers)
        self.bans = ChatApiBase(config, endpoint.bans)
        self.departments = ChatApiBase(config, endpoint.departments)
        self.goals = ChatApiBase(config, endpoint.goals)
        self.stream = ChatApiBase(config, endpoint.stream)

    def search(self, *args, **kwargs):
        url = self._build_url(self.endpoint.search(*args, **kwargs))
        return self._get(url)


class HelpCentreApiBase(Api):
    def __init__(self, config, endpoint, object_type):
        super(HelpCentreApiBase, self).__init__(config, object_type=object_type, endpoint=endpoint)

        self._response_handlers = (MissingTranslationHandler,) + self._response_handlers

        self._object_mapping = HelpCentreObjectMapping(self)
        self.locale = ''

    def _process_response(self, response, object_mapping=None):
        endpoint_path = get_endpoint_path(self, response)
        if endpoint_path.startswith('/help_center') or endpoint_path.startswith('/community'):
            object_mapping = self._object_mapping
        else:
            object_mapping = ZendeskObjectMapping(self)
        return super(HelpCentreApiBase, self)._process_response(response, object_mapping)

    def _build_url(self, endpoint):
        return super(HelpCentreApiBase, self)._build_url(endpoint)


class TranslationApi(Api):
    @extract_id(Article, Section, Category)
    def translations(self, help_centre_object):
        return self._query_zendesk(self.endpoint.translations, object_type='translation', id=help_centre_object)

    @extract_id(Article, Section, Category)
    def missing_translations(self, help_centre_object):
        return self._query_zendesk(self.endpoint.missing_translations, object_type='translation', id=help_centre_object)

    @extract_id(Article, Section, Category)
    def create_translation(self, help_centre_object, translation):
        return TranslationRequest(self).post(self.endpoint.create_translation, help_centre_object, translation)

    @extract_id(Article, Section, Category)
    def update_translation(self, help_centre_object, translation):
        return TranslationRequest(self).put(self.endpoint.update_translation, help_centre_object, translation)

    @extract_id(Translation)
    def delete_translation(self, translation):
        return TranslationRequest(self).delete(self.endpoint.delete_translation, translation)


class SubscriptionApi(Api):
    @extract_id(Article, Section, Post, Topic)
    def subscriptions(self, help_centre_object):
        return self._query_zendesk(self.endpoint.subscriptions, object_type='subscriptions', id=help_centre_object)

    @extract_id(Article, Section, Post, Topic)
    def create_subscription(self, help_centre_object, subscription):
        return SubscriptionRequest(self).post(self.endpoint.subscriptions, help_centre_object, subscription)

    @extract_id(Article, Section, Post, Topic, Subscription)
    def delete_subscription(self, help_centre_object, subscription):
        return SubscriptionRequest(self).delete(self.endpoint.subscriptions_delete, help_centre_object, subscription)


class VoteApi(Api):
    @extract_id(Article, Post, Comment)
    def votes(self, help_centre_object):
        url = self._build_url(self.endpoint.votes(id=help_centre_object))
        return self._get(url)

    @extract_id(Article, Post, Comment)
    def vote_up(self, help_centre_object):
        url = self._build_url(self.endpoint.votes.up(id=help_centre_object))
        return self._post(url, payload={})

    @extract_id(Article, Post, Comment)
    def vote_down(self, help_centre_object):
        url = self._build_url(self.endpoint.votes.down(id=help_centre_object))
        return self._post(url, payload={})


class VoteCommentApi(Api):
    @extract_id(Article, Post, Comment)
    def comment_votes(self, help_centre_object, comment):
        url = self._build_url(self.endpoint.comment_votes(help_centre_object, comment))
        return self._get(url)

    @extract_id(Article, Post, Comment)
    def vote_comment_up(self, help_centre_object, comment):
        url = self._build_url(self.endpoint.comment_votes.up(help_centre_object, comment))
        return self._post(url, payload={})

    @extract_id(Article, Post, Comment)
    def vote_comment_down(self, help_centre_object, comment):
        url = self._build_url(self.endpoint.comment_votes.down(help_centre_object, comment))
        return self._post(url, payload={})


class ArticleApi(HelpCentreApiBase, TranslationApi, SubscriptionApi, VoteApi, VoteCommentApi, IncrementalApi):
    @extract_id(Section)
    def create(self, section, article):
        """
        Create (POST) an Article - See: Zendesk API `Reference
        <https://developer.zendesk.com/rest_api/docs/help_center/articles#create-article>`__.

        :param section: Section ID or object
        :param article: Article to create
        """
        return CRUDRequest(self).post(article, create=True, id=section)

    def update(self, article):
        """
        Update (PUT) and Article - See: Zendesk API `Reference
        <https://developer.zendesk.com/rest_api/docs/help_center/articles#update-article>`__.

        :param article: Article to update
        """
        return CRUDRequest(self).put(article)

    def archive(self, article):
        """
        Archive (DELETE) an Article - See: Zendesk API `Reference
        <https://developer.zendesk.com/rest_api/docs/help_center/articles#archive-article>`__.

        :param article: Article to archive
        """
        return CRUDRequest(self).delete(article)

    @extract_id(Article)
    def comments(self, article):
        """
        Retrieve comments for an article

        :param article: Article ID or object
        """
        return self._query_zendesk(self.endpoint.comments, object_type='comment', id=article)

    @extract_id(Article)
    def labels(self, article):
        return self._query_zendesk(self.endpoint.labels, object_type='label', id=article)

    @extract_id(Article)
    def show_translation(self, article, locale):
        url = self._build_url(self.endpoint.show_translation(article, locale))
        return self._get(url)

    def search(self, *args, **kwargs):
        url = self._build_url(self.endpoint.search(*args, **kwargs))
        return self._get(url)


class CommentApi(HelpCentreApiBase):
    def __call__(self, *args, **kwargs):
        raise ZenpyException("You cannot directly call this Api!")

    @extract_id(Article, Comment)
    def show(self, article, comment):
        url = self._build_url(self.endpoint.comment_show(article, comment))
        return self._get(url)

    @extract_id(Article)
    def create(self, article, comment):
        if comment.locale is None:
            raise ZenpyException(
                "locale is required when creating comments - "
                "https://developer.zendesk.com/rest_api/docs/help_center/comments#create-comment"
            )
        return HelpdeskCommentRequest(self).post(self.endpoint.comments, article, comment)

    @extract_id(Article)
    def update(self, article, comment):
        return HelpdeskCommentRequest(self).put(self.endpoint.comments_update, article, comment)

    @extract_id(Article, Comment)
    def delete(self, article, comment):
        return HelpdeskCommentRequest(self).delete(self.endpoint.comments_delete, article, comment)

    @extract_id(User)
    def user_comments(self, user):
        return self._query_zendesk(self.endpoint.user_comments, object_type='comment', id=user)


class CategoryApi(HelpCentreApiBase, CRUDApi, TranslationApi):
    def articles(self, category_id):
        return self._query_zendesk(self.endpoint.articles, 'article', id=category_id)

    def sections(self, category_id):
        return self._query_zendesk(self.endpoint.sections, 'section', id=category_id)


class AccessPolicyApi(Api):
    @extract_id(Topic, Section)
    def access_policies(self, help_centre_object):
        return self._query_zendesk(self.endpoint.access_policies, 'access_policy', id=help_centre_object)

    @extract_id(Topic, Section)
    def update_access_policy(self, help_centre_object, access_policy):
        return AccessPolicyRequest(self).put(self.endpoint.access_policies, help_centre_object, access_policy)


class SectionApi(HelpCentreApiBase, CRUDApi, TranslationApi, SubscriptionApi, AccessPolicyApi):
    @extract_id(Section)
    def articles(self, section):
        return self._query_zendesk(self.endpoint.articles, 'article', id=section)

    def create(self, section):
        return CRUDRequest(self).post(section, create=True, id=section.category_id)


class ArticleAttachmentApi(HelpCentreApiBase, SubscriptionApi):
    @extract_id(Article)
    def __call__(self, article):
        """
        Returns all attachments associated with article_id either ``inline=True`` or ``inline=False``.

        :param article: Numeric article id or :class:`Article` object.
        :return: Generator with all associated articles attachments.
        """
        return self._query_zendesk(self.endpoint, 'article_attachment', id=article)

    @extract_id(Article)
    def inline(self, article):
        """
        Returns all inline attachments associated with article_id where (Such attachments has ``inline=True`` flag).

        Inline attachments and its url can be referenced in the HTML body of the article.

        :param article: Numeric article id or :class:`Article` object.
        :return: Generator with all associated inline attachments.
        """
        return self._query_zendesk(self.endpoint.inline, 'article_attachment', id=article)

    @extract_id(Article)
    def block(self, article):
        """
        Returns all block attachments associated with article_id (Such attachments has ``inline=False``).

        Block attachments are displayed as separated files attached to Article.

        :param article: Numeric article id or :class:`Article` object.
        :return: Generator with all associated block attachments.
        """
        return self._query_zendesk(self.endpoint.block, 'article_attachment', id=article)

    @extract_id(ArticleAttachment)
    def show(self, attachment):
        return self._query_zendesk(self.endpoint, 'article_attachment', id=attachment)

    @extract_id(Article)
    def create(self, article, attachment, inline=False, file_name=None, content_type=None):
        """
        This function creates attachment attached to article.

        :param article: Numeric article id or :class:`Article` object.
        :param attachment: File object or os path to file
        :param inline: If true, the attached file is shown in the dedicated admin UI
            for inline attachments and its url can be referenced in the HTML body of
            the article. If false, the attachment is listed in the list of attachments.
            Default is `false`
        :param file_name: you can set filename on file upload.
        :param content_type: The content type of the file. `Example: image/png`, Zendesk can ignore it.
        :return: :class:`ArticleAttachment` object
        """
        return HelpdeskAttachmentRequest(self).post(self.endpoint.create,
                                                    article=article,
                                                    attachments=attachment,
                                                    inline=inline,
                                                    file_name=file_name,
                                                    content_type=content_type)

    def create_unassociated(self, attachment, inline=False, file_name=None, content_type=None):
        """
        You can use this endpoint for bulk imports.
        It lets you upload a file without associating it to an article until later.
        Check Zendesk documentation `important notes
        <https://developer.zendesk.com/rest_api/docs/help_center/article_attachments#create-unassociated-attachment>

        :param attachment: File object or os path to file
        :param inline: If true, the attached file is shown in the dedicated admin UI
            for inline attachments and its url can be referenced in the HTML body of
            the article. If false, the attachment is listed in the list of attachments.
            Default is `false`
        :param file_name: you can set filename on file upload.
        :param content_type: The content type of the file. `Example: image/png`, Zendesk can ignore it.
        :return: :class:`ArticleAttachment` object
        """
        return HelpdeskAttachmentRequest(self).post(self.endpoint.create_unassociated,
                                                    attachments=attachment,
                                                    inline=inline,
                                                    file_name=file_name,
                                                    content_type=content_type)

    @extract_id(ArticleAttachment)
    def delete(self, article_attachment):
        """
        This function completely wipes attachment from Zendesk Helpdesk article.

        :param article_attachment: :class:`ArticleAttachment` object or numeric article attachment id.
        :return: status_code == 204 on success
        """
        return HelpdeskAttachmentRequest(self).delete(self.endpoint.delete, article_attachment)

    @extract_id(Article)
    def bulk_attachments(self, article, attachments):
        """
        This function implements associating attachments to an article after article creation (for
        unassociated attachments).

        :param article: Article id or :class:`Article` object
        :param attachments: :class:`ArticleAttachment` object, or list of :class:`ArticleAttachment` objects,
        up to 20 supported. `Zendesk documentation.
        <https://developer.zendesk.com/rest_api/docs/help_center/articles#associate-attachments-in-bulk-to-article>`__
        :return:
        """
        return HelpdeskAttachmentRequest(self).post(self.endpoint.bulk_attachments, article=article,
                                                    attachments=attachments)

class LabelApi(HelpCentreApiBase):
    @extract_id(Article)
    def create(self, article, label):
        return HelpCentreRequest(self).post(self.endpoint.create, article, label)

    @extract_id(Article, Label)
    def delete(self, article, label):
        return HelpCentreRequest(self).delete(self.endpoint.delete, article, label)


class TopicApi(HelpCentreApiBase, CRUDApi, SubscriptionApi):
    @extract_id(Topic)
    def posts(self, topic):
        url = self._build_url(self.endpoint.posts(id=topic))
        return self._get(url)


class PostCommentApi(HelpCentreApiBase, VoteCommentApi):
    @extract_id(Post)
    def __call__(self, post):
        return super(PostCommentApi, self).__call__(id=post)

    @extract_id(Post)
    def create(self, post, comment):
        return PostCommentRequest(self).post(self.endpoint, post, comment)

    @extract_id(Post)
    def update(self, post, comment):
        return PostCommentRequest(self).put(self.endpoint.update, post, comment)

    @extract_id(Post, Comment)
    def delete(self, post, comment):
        return PostCommentRequest(self).delete(self.endpoint.delete, post, comment)


class PostApi(HelpCentreApiBase, CRUDApi, SubscriptionApi, VoteApi):
    def __init__(self, config, endpoint, object_type):
        super(PostApi, self).__init__(config, endpoint, object_type)
        self.comments = PostCommentApi(config, endpoint.comments, 'post')


class UserSegmentApi(HelpCentreApiBase, CRUDApi):
    def applicable(self):
        return self._query_zendesk(self.endpoint.applicable, object_type='user_segment')

    @extract_id(Section)
    def sections(self, section):
        return self._query_zendesk(self.endpoint.sections, object_type='section', id=section)

    @extract_id(Topic)
    def topics(self, topic):
        return self._query_zendesk(self.endpoint.topics, object_type='topic', id=topic)


class HelpCentreApi(HelpCentreApiBase):
    def __init__(self, config):
        super(HelpCentreApi, self).__init__(config, endpoint=EndpointFactory('help_centre'), object_type='help_centre')

        self.articles = ArticleApi(config, self.endpoint.articles, object_type='article')
        self.comments = CommentApi(config, self.endpoint.articles, object_type='comment')
        self.sections = SectionApi(config, self.endpoint.sections, object_type='section')
        self.categories = CategoryApi(config, self.endpoint.categories, object_type='category')
        self.attachments = ArticleAttachmentApi(config, self.endpoint.attachments, object_type='article_attachment')
        self.labels = LabelApi(config, self.endpoint.labels, object_type='label')
        self.topics = TopicApi(config, self.endpoint.topics, object_type='topic')
        self.posts = PostApi(config, self.endpoint.posts, object_type='post')
        self.user_segments = UserSegmentApi(config, self.endpoint.user_segments, object_type='user_segment')

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("Cannot directly call the HelpCentreApi!")


class NpsApi(Api):
    def __init__(self, config):
        super(NpsApi, self).__init__(config, object_type='nps')

    def __call__(self, *args, **kwargs):
        raise ZenpyException("You cannot call this endpoint directly!")

    def recipients_incremental(self, start_time):
        """
        Retrieve NPS Recipients incremental

        :param start_time: time to retrieve events from.
        """
        return self._query_zendesk(self.endpoint.recipients_incremental, 'recipients', start_time=start_time)

    def responses_incremental(self, start_time):
        """
        Retrieve NPS Responses incremental

        :param start_time: time to retrieve events from.
        """
        return self._query_zendesk(self.endpoint.responses_incremental, 'responses', start_time=start_time)

class TalkApiBase(Api):
    def __init__(self, config, endpoint, object_type):
        super(TalkApiBase, self).__init__(config, object_type=object_type, endpoint=endpoint)

        self._object_mapping = TalkObjectMapping(self)

    def _build_url(self, endpoint):
        return super(TalkApiBase, self)._build_url(endpoint)

class TalkApi(TalkApiBase):
    def __init__(self, config):
        super(TalkApi, self).__init__(config, endpoint=EndpointFactory('talk'), object_type='talk')

        self.current_queue_activity = StatsApi(config, self.endpoint.current_queue_activity, object_type='current_queue_activity')
        self.agents_activity = StatsApi(config, self.endpoint.agents_activity, object_type='agents_activity')
        self.availability = AvailabilitiesApi(config, self.endpoint.availability, object_type='availability')
        self.account_overview = StatsApi(config, self.endpoint.account_overview, object_type='account_overview')
        self.phone_numbers = PhoneNumbersApi(config, self.endpoint.phone_numbers, object_type='phone_numbers')
        self.agents_overview = StatsApi(config, self.endpoint.agents_overview, object_type='agents_overview')

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("Cannot directly call the TalkApi!")

class StatsApi(TalkApiBase):
    def __init__(self, config, endpoint, object_type):
             super(StatsApi, self).__init__(config, object_type=object_type, endpoint=endpoint)

class AvailabilitiesApi(TalkApiBase):
    def __init__(self, config, endpoint, object_type):
             super(AvailabilitiesApi, self).__init__(config, object_type=object_type, endpoint=endpoint)

class PhoneNumbersApi(TalkApiBase):
    def __init__(self, config, endpoint, object_type):
             super(PhoneNumbersApi, self).__init__(config, object_type=object_type, endpoint=endpoint)

class CustomAgentRolesApi(CRUDApi):
    pass
