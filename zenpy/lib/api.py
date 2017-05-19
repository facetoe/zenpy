import json
import logging
from datetime import datetime, date
from time import sleep, time

from json import JSONEncoder

from zenpy.lib.api_objects import User, Macro, Identity, View
from zenpy.lib.cache import query_cache
from zenpy.lib.exception import *
from zenpy.lib.mapping import ZendeskObjectMapping, ChatObjectMapping
from zenpy.lib.request import *
from zenpy.lib.response import *
from zenpy.lib.util import as_plural

__author__ = 'facetoe'

log = logging.getLogger(__name__)


class ZenpyObjectEncoder(JSONEncoder):
    """ Class for encoding API objects"""

    def default(self, o):
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        elif isinstance(o, datetime):
            return o.date().isoformat()
        elif isinstance(o, date):
            return o.isoformat()


class BaseApi(object):
    """
    Base class for API. Responsible for submitting requests to Zendesk, controlling
    rate limiting and deserializing responses.
    """

    def __init__(self, subdomain, session, timeout, ratelimit, ratelimit_budget):
        self.subdomain = subdomain
        self.session = session
        self.timeout = timeout
        self.ratelimit = ratelimit
        self.ratelimit_budget = ratelimit_budget
        self.protocol = 'https'
        self.api_prefix = 'api/v2'
        self._url_template = "%(protocol)s://%(subdomain)s.zendesk.com/%(api_prefix)s"
        self.callsafety = {
            'lastcalltime': None,
            'lastlimitremaining': None
        }
        self._response_handlers = (
            DeleteResponseHandler,
            TagResponseHandler,
            SearchResponseHandler,
            CombinationResponseHandler,
            ViewResponseHandler,
            SlaPolicyResponseHandler,
            GenericZendeskResponseHandler,
            HTTPOKResponseHandler,
        )

    def _post(self, url, payload, data=None):
        headers = {'Content-Type': 'application/octet-stream'} if data else None
        response = self._call_api(self.session.post, url,
                                  json=self._serialize(payload),
                                  data=data,
                                  headers=headers,
                                  timeout=self.timeout)
        return self._process_response(response)

    def _put(self, url, payload):
        response = self._call_api(self.session.put, url, json=self._serialize(payload), timeout=self.timeout)
        return self._process_response(response)

    def _delete(self, url, payload=None):
        response = self._call_api(self.session.delete, url, json=payload, timeout=self.timeout)
        return self._process_response(response)

    def _get(self, url, raw_response=False):
        response = self._call_api(self.session.get, url, timeout=self.timeout)
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
                log.warn(
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

        if time_since_last_call() is None or time_since_last_call() >= 10 or lastlimitremaining >= self.ratelimit:
            response = http_method(url, **kwargs)
        else:
            # We hit our limit floor and aren't quite at 10 seconds yet..
            log.warn(
                "Safety Limit Reached of %s remaining calls and time since last call is under 10 seconds"
                % self.ratelimit
            )
            while time_since_last_call() < 10:
                remaining_sleep = int(10 - time_since_last_call())
                log.debug("  -> sleeping: %s more seconds" % remaining_sleep)
                sleep(1)
            response = http_method(url, **kwargs)

        self.callsafety['lastcalltime'] = time()
        self.callsafety['lastlimitremaining'] = response.headers.get('X-Rate-Limit-Remaining', 0)
        return response

    def _update_callsafety(self, response):
        """ Update the callsafety data structure """
        if self.ratelimit is not None:
            self.callsafety['lastcalltime'] = time()
            self.callsafety['lastlimitremaining'] = int(response.headers.get('X-Rate-Limit-Remaining', 0))

    def _process_response(self, response):
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
                return handler(self).build(response)
        raise ZenpyException("Could not handle response: {}".format(pretty_response))

    def _serialize(self, zenpy_object):
        """ Serialize a Zenpy object to JSON """
        return json.loads(json.dumps(zenpy_object, cls=ZenpyObjectEncoder))

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
            item = query_cache(object_type, _id)
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
                obj = query_cache(object_type, _id)
                if obj:
                    cached_objects.append(obj)
                else:
                    return self._get(self._build_url(endpoint=endpoint(*endpoint_args, **endpoint_kwargs)))
            return cached_objects
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

    def _build_url(self, endpoint=''):
        """ Build complete URL """
        if not issubclass(type(self), ChatApiBase) and not self.subdomain:
            raise ZenpyException("subdomain is required when accessing the Zendesk API!")
        return "/".join((self._url_template % vars(self), endpoint))


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

    def append_sideload(self, sideload, method_name=None):
        """ Append a sideload to the list of sideloads. """
        self.get_sideloads(method_name).append(sideload)

    def remove_sideload(self, sideload, method_name=None):
        """ Remove a sideload from the list of sideloads. """
        self.get_sideloads(method_name).remove(sideload)

    def get_sideloads(self, method_name=None):
        """
        Return the list of sideloads for this API. If method_name is passed,
        return the list of sideloads available to that method. For example:
            zenpy_client.tickets.get_sideloads(method_name='incremental')
        will return the sideloads for the incremental method.
        """
        if method_name:
            if not hasattr(self.endpoint, method_name):
                raise ZenpyException("{} has no method named '{}'".format(self.endpoint, method_name))
            return getattr(self.endpoint, method_name).sideload
        else:
            return self.endpoint.sideload

    def __call__(self, *args, **kwargs):
        return self._query_zendesk(self.endpoint, self.object_type, *args, **kwargs)

    def _get_user(self, user_id):
        return self._query_zendesk(EndpointFactory.users, 'user', id=user_id)

    def _get_users(self, user_ids):
        return self._query_zendesk(endpoint=EndpointFactory.users, object_type='user', ids=user_ids)

    def _get_comment(self, comment_id):
        return self._query_zendesk(endpoint=EndpointFactory.tickets.comments, object_type='comment', id=comment_id)

    def _get_organization(self, organization_id):
        return self._query_zendesk(endpoint=EndpointFactory.organizations, object_type='organization',
                                   id=organization_id)

    def _get_group(self, group_id):
        return self._query_zendesk(endpoint=EndpointFactory.groups, object_type='group', id=group_id)

    def _get_brand(self, brand_id):
        return self._query_zendesk(endpoint=EndpointFactory.brands, object_type='brand', id=brand_id)

    def _get_ticket(self, ticket_id):
        return self._query_zendesk(endpoint=EndpointFactory.tickets, object_type='ticket', id=ticket_id)

    def _get_sharing_agreements(self, sharing_agreement_ids):
        sharing_agreements = []
        for _id in sharing_agreement_ids:
            sharing_agreement = self._query_zendesk(endpoint=EndpointFactory.sharing_agreements,
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
        return CRUDRequest(self).perform("POST", api_objects)

    def update(self, api_objects, **kwargs):
        """
        Update (PUT) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param api_objects: object or objects to update
        """
        return CRUDRequest(self).perform("PUT", api_objects)

    def delete(self, api_objects, **kwargs):
        """
        Delete (DELETE) one or more API objects. After successfully deleting the objects from the API
        they will also be removed from the relevant Zenpy caches.

        :param api_objects: object or objects to delete
        """

        return CRUDRequest(self).perform("DELETE", api_objects)


class SuspendedTicketApi(Api):
    """
    The SuspendedTicketApi adds some SuspendedTicket specific functionality
    """

    def recover(self, tickets):
        """
        Recover (PUT) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to recover
        """
        return SuspendedTicketRequest(self).perform("PUT", tickets)

    def delete(self, tickets):
        """
        Delete (DELETE) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to delete
        """
        return SuspendedTicketRequest(self).perform("DELETE", tickets)


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
        return TagRequest(self).perform("PUT", tags, id)

    def set_tags(self, id, tags):
        """
        Set (POST) one or more tags.

        :param _id: the id of the object to tag
        :param tags: array of tags to apply to object
        """
        return TagRequest(self).perform("POST", tags, id)

    def delete_tags(self, id, tags):
        """
        Delete (DELETE) one or more tags.

        :param _id: the id of the object to delete tag from
        :param tags: array of tags to delete from object
        """
        return TagRequest(self).perform("DELETE", tags, id)

    def tags(self, _id):
        """
        Lists the most popular recent tags in decreasing popularity
        """
        return self._query_zendesk(self.endpoint.tags, 'tag', id=_id)


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
        return RateRequest(self).perform("POST", rating, id)


class IncrementalApi(Api):
    """
    IncrementalApi supports the incremental endpoint.
    """

    def incremental(self, start_time):
        """
        Retrieve bulk data from the incremental API.
        :param start_time: The time of the oldest object you are interested in.
        """
        return self._query_zendesk(self.endpoint.incremental, self.object_type, start_time=start_time)


class UserIdentityApi(Api):
    def __init__(self, config):
        super(UserIdentityApi, self).__init__(config,
                                              object_type='identity',
                                              endpoint=EndpointFactory('users').identities)

    def show(self, user, identity):
        """
        Show the specified identity for the specified user.

        :param user: user id or User object
        :param identity: identity id object
        :return: Identity
        """
        if isinstance(user, User):
            user = user.id
        if isinstance(identity, Identity):
            identity = identity.id

        url = self.endpoint.show(user, identity)
        return self._get(url)

    def create(self, user, identity):
        """
        Create an additional identity for the specified user

        :param user: User id or object
        :param identity: Identity object to be created
        """
        if not isinstance(identity, Identity):
            raise ZenpyException("Invalid type - expected Identity received: {}".format(type(identity)))
        if isinstance(user, User):
            user = user.id
        return UserIdentityRequest(self).perform("POST", user, identity)

    def update(self, user, identity):
        """
        Update specified identity for the specified user

        :param user: User object or id
        :param identity: Identity object to be updated.
        :return: The updated Identity
        """
        if not isinstance(identity, Identity):
            raise ZenpyException("You must pass an Identity object to this endpoint!")
        if isinstance(user, User):
            user = user.id
        return UserIdentityRequest(self).perform("PUT", self.endpoint.update, user, identity.id)

    def make_primary(self, user, identity):
        """
        Set the specified user as primary for the specified user.

        :param user: User object or id
        :param identity: Identity object or id
        :return: list of user's Identities
        """
        if isinstance(user, User):
            user = user.id
        if isinstance(identity, Identity):
            identity = identity.id
        return UserIdentityRequest(self).perform("PUT", self.endpoint.make_primary, user, identity)

    def request_verification(self, user, identity):
        """
        Sends the user a verification email with a link to verify ownership of the email address.

        :param user: User id or object
        :param identity: Identity id or object
        :return: requests Response object
        """
        if isinstance(user, User):
            user = user.id
        if isinstance(identity, Identity):
            identity = identity.id

        return UserIdentityRequest(self).perform("PUT", self.endpoint.request_verification, user, identity)

    def verify(self, user, identity):
        """
        Verify an identity for a user

        :param user: User id or object
        :param identity: Identity id or object
        :return: the verified Identity
        """
        if isinstance(user, User):
            user = user.id
        if isinstance(identity, Identity):
            identity = identity.id
        return UserIdentityRequest(self).perform("PUT", self.endpoint.verify, user, identity)

    def delete(self, user, identity):
        """
        Deletes the identity for a given user

        :param user: User id or object
        :param identity: Identity id or object
        :return: requests Response object
        """
        if isinstance(user, User):
            user = user.id
        if isinstance(identity, Identity):
            identity = identity.id
        return UserIdentityRequest(self).perform("DELETE", user, identity)


class UserApi(IncrementalApi, CRUDApi):
    """
    The UserApi adds some User specific functionality
    """

    def __init__(self, config):
        super(UserApi, self).__init__(config, object_type='user')
        self.identities = UserIdentityApi(config)

    def groups(self, user_id):
        """
        Retrieve the groups for this user.

        :param user_id: user id
        """
        return self._query_zendesk(self.endpoint.groups, 'group', id=user_id)

    def organizations(self, user_id):
        """
        Retrieve the organizations for this user.

        :param user_id: user id
        """
        return self._query_zendesk(self.endpoint.organizations, 'organization', id=user_id)

    def requested(self, user_id):
        """
        Retrieve the requested tickets for this user.

        :param user_id: user id
        """
        return self._query_zendesk(self.endpoint.requested, 'ticket', id=user_id)

    def cced(self, user_id):
        """
        Retrieve the tickets this user is cc'd into.

        :param user_id: user id
        """
        return self._query_zendesk(self.endpoint.cced, 'ticket', id=user_id)

    def assigned(self, user_id):
        """
        Retrieve the assigned tickets for this user.

        :param user_id: user id
        """
        return self._query_zendesk(self.endpoint.assigned, 'ticket', id=user_id)

    def group_memberships(self, user_id):
        """
        Retrieve the group memberships for this user.

        :param user_id: user id
        """
        return self._query_zendesk(self.endpoint.group_memberships, 'group_membership', id=user_id)

    def requests(self, **kwargs):
        return self._query_zendesk(self.endpoint.requests, 'request', **kwargs)

    def related(self, user_id):
        """
        Returns the UserRelated information for the requested User

        :param user_id: User id
        :return: UserRelated
        """
        return self._query_zendesk(self.endpoint.related, 'user_related', id=user_id)

    def me(self):
        """
        Return the logged in user
        """
        return self._query_zendesk(self.endpoint.me, 'user', id=None)

    def merge(self, source_user, dest_user):
        """
        Merge the user provided in source_user into dest_user

        :param source_user: User object or id of user to be merged
        :param dest_user: User object or id to merge into
        :return: The merged User
        """
        return UserMergeRequest(self).perform("PUT", source_user, dest_user)

    def user_fields(self, user_id):
        """
        Retrieve the user fields for this user.

        :param user_id: user id
        """
        return self._query_zendesk(self.endpoint.user_fields, 'user_field', id=user_id)

    def organization_memberships(self, user_id):
        """
        Retrieve the organization memberships for this user.

        :param user_id: user id
        """
        return self._query_zendesk(self.endpoint.organization_memberships, 'organization_membership', id=user_id)

    def create_or_update(self, users):
        """
        Creates a user (POST) if the user does not already exist, or updates an existing user identified
        by e-mail address or external ID.

        :param users: User object or list of User objects
        :return: the created/updated User or a  JobStatus object if a list was passed
        """

        return CRUDRequest(self).perform("POST", users, create_or_update=True)


class AttachmentApi(Api):
    def __init__(self, config):
        super(AttachmentApi, self).__init__(config, object_type='attachment')

    def __call__(self, *args, **kwargs):
        if 'id' not in kwargs:
            raise ZenpyException("Attachment endpoint requires an id")
        return Api.__call__(self, **kwargs)

    def upload(self, fp, token=None, target_name=None):
        """
        Upload a file to Zendesk.

        :param fp: file object, StringIO instance, content, or file path to be
                   uploaded
        :param token: upload token for uploading multiple files
        :param target_name: name of the file inside Zendesk
        :return: :class:`Upload` object containing a token and other information
                    (see https://developer.zendesk.com/rest_api/docs/core/attachments#uploading-files)
        """
        return UploadRequest(self).perform("POST", fp, token=token, target_name=target_name)


class EndUserApi(CRUDApi):
    """
    EndUsers can only update.
    """

    def __init__(self, config):
        super(EndUserApi, self).__init__(config, object_type='user')

    def delete(self, api_objects, **kwargs):
        raise ZenpyException("EndUsers cannot delete!")

    def create(self, api_objects, **kwargs):
        raise ZenpyException("EndUsers cannot create!")


class OrganizationApi(TaggableApi, IncrementalApi, CRUDApi):
    def __init__(self, config):
        super(OrganizationApi, self).__init__(config, object_type='organization')

    def organization_fields(self, org_id):
        """
        Retrieve the organization fields for this organization.

        :param org_id: organization id
        """
        return self._query_zendesk(self.endpoint.organization_fields, 'organization_field', id=org_id)

    def organization_memberships(self, org_id):
        """
        Retrieve the organization fields for this organization.

        :param org_id: organization id
        """
        return self._query_zendesk(self.endpoint.organization_memberships, 'organization_membership', id=org_id)

    def external(self, external_id):
        """
        Locate an Organization by it's external_id attribute.

        :param external_id: external id of organization
        """
        return self._query_zendesk(self.endpoint.external, 'organization', id=external_id)

    def requests(self, **kwargs):
        return self._query_zendesk(self.endpoint.requests, 'request', **kwargs)

    def create_or_update(self, organization):
        """
        Creates an organization if it doesn't already exist, or updates an existing
        organization identified by ID or external ID

        :param organization: Organization object
        :return: the created/updated Organization
        """

        return CRUDRequest(self).perform("POST", organization, create_or_update=True)


class OrganizationMembershipApi(CRUDApi):
    """
    The OrganizationMembershipApi allows the creation and deletion of Organization Memberships
    """

    def __init__(self, config):
        super(OrganizationMembershipApi, self).__init__(config, object_type='organization_membership')

    def update(self, items, **kwargs):
        raise ZenpyException("You cannot update Organization Memberships!")


class SatisfactionRatingApi(Api):
    def __init__(self, config):
        super(SatisfactionRatingApi, self).__init__(config, object_type='satisfaction_rating')

    def create(self, ticket_id, satisfaction_rating):
        """
        Create/update a Satisfaction Rating for a ticket.

        :param ticket_id: id of Ticket to rate
        :param satisfaction_rating: SatisfactionRating object.
        """
        return SatisfactionRatingRequest(self).perform("POST", ticket_id, satisfaction_rating)


class MacroApi(CRUDApi):
    def __init__(self, config):
        super(MacroApi, self).__init__(config, object_type='macro')

    def apply(self, macro_id):
        """
        Show what a macro would do - https://developer.zendesk.com/rest_api/docs/core/macros#show-changes-to-ticket

        :param macro_id: id of macro to test
        """

        return self._query_zendesk(self.endpoint.apply, 'result', id=macro_id)


class TicketApi(RateableApi, TaggableApi, IncrementalApi, CRUDApi):
    """
    The TicketApi adds some Ticket specific functionality
    """

    def __init__(self, config):
        super(TicketApi, self).__init__(config, object_type='ticket')

    def organizations(self, org_id):
        """
        Retrieve the tickets for this organization.

        :param org_id: organization id
        """
        return self._query_zendesk(self.endpoint.organizations, 'ticket', id=org_id)

    def recent(self):
        """
        Retrieve the most recent tickets
        """
        return self._query_zendesk(self.endpoint.recent, 'ticket', id=None)

    def comments(self, ticket_id):
        """
        Retrieve the comments for a ticket.

        :param ticket_id: ticket id
        """
        return self._query_zendesk(self.endpoint.comments, 'comment', id=ticket_id)

    def events(self, start_time):
        """
        Retrieve TicketEvents
        :param start_time: time to retrieve events from.
        """
        return self._query_zendesk(self.endpoint.events, 'ticket_event', start_time=start_time)

    def audits(self, ticket_id):
        """
        Retrieve TicketAudits.
        :param ticket_id: ticket id
        """
        return self._query_zendesk(self.endpoint.audits, 'ticket_audit', id=ticket_id)

    def metrics(self, ticket_id):
        """
        Retrieve TicketMetric.
        :param ticket_id: ticket id
        """
        return self._query_zendesk(self.endpoint.metrics, 'ticket_metric', id=ticket_id)

    def metrics_incremental(self, start_time):
        """
        Retrieve TicketMetric incremental
        :param start_time: time to retrieve events from.
        """
        return self._query_zendesk(self.endpoint.metrics.incremental, 'ticket_metric_events', start_time=start_time)

    def show_macro_effect(self, ticket, macro):
        """
        Apply macro to ticket. Returns what it *would* do, does not alter the ticket.

        :param ticket: Ticket or ticket id to target
        :param macro: Macro or macro id to use
        """

        if isinstance(ticket, Ticket):
            ticket = ticket.id
        if isinstance(macro, Macro):
            macro = macro.id
        url = self._build_url(self.endpoint.macro(ticket, macro))
        return self._get(url)

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
        return TicketMergeRequest(self).perform("POST", target, source,
                                                target_comment=target_comment,
                                                source_comment=source_comment)


class TicketImportAPI(CRUDApi):
    def __init__(self, config):
        super(TicketImportAPI, self).__init__(config,
                                              object_type='ticket',
                                              endpoint=EndpointFactory('ticket_import'))

    def __call__(self, *args, **kwargs):
        raise ZenpyException("You must pass ticket objects to this endpoint!")

    def update(self, items, **kwargs):
        raise ZenpyException("You cannot update objects using ticket_import endpoint!")

    def delete(self, api_objects, **kwargs):
        raise ZenpyException("You cannot delete objects using the ticket_import endpoint!")


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
        Search for requests. See the Zendesk docs for more information on the syntax
         https://developer.zendesk.com/rest_api/docs/core/requests#searching-requests
        """
        return self._query_zendesk(self.endpoint.search, 'request', *args, **kwargs)


class SharingAgreementAPI(CRUDApi):
    def __init__(self, config):
        super(SharingAgreementAPI, self).__init__(config, object_type='sharing_agreement')


class GroupApi(CRUDApi):
    def __init__(self, config):
        super(GroupApi, self).__init__(config, object_type='group')


class ViewApi(CRUDApi):
    def __init__(self, config):
        super(ViewApi, self).__init__(config, object_type='view')

    def active(self):
        """
        Return all active views.
        """
        return self._get(self._build_url(self.endpoint.active()))

    def compact(self):
        """
        Return compact views - https://developer.zendesk.com/rest_api/docs/core/views#list-views---compact
        """
        return self._get(self._build_url(self.endpoint.compact()))

    def execute(self, view):
        """
        Execute a view.

        :param view: View or view id
        """
        if isinstance(view, View):
            view = view.id
        return self._get(self._build_url(self.endpoint.execute(id=view)))

    def tickets(self, view):
        """
        Return the tickets in a view.

        :param view: View or view id
        """
        if isinstance(view, View):
            view = view.id
        return self._get(self._build_url(self.endpoint.tickets(id=view)))

    def count(self, view):
        """
        Return a ViewCount for a view.

        :param view: View or view id
        """
        if isinstance(view, View):
            view = view.id
        return self._get(self._build_url(self.endpoint(id=view)))

    def count_many(self, views):
        """
        Return many ViewCounts.

        :param views: iterable of View or view ids
        """
        if not isinstance(views, collections.Iterable):
            raise ZenpyException("count_many() requires an iterable!")
        ids = []
        for v in views:
            ids.append(v.id if isinstance(v, View) else v)
        return self._get(self._build_url(self.endpoint(count_many=ids)))

    def export(self, view):
        """
        Export a view. Returns an Export object.

        :param view: View or view id
        :return:
        :return:
        """
        if isinstance(view, View):
            view = view.id
        return self._get(self._build_url(self.endpoint.export(id=view)))

    def search(self, *args, **kwargs):
        """
        Search views. See - https://developer.zendesk.com/rest_api/docs/core/views#search-views.

        :param args: query is the only accepted arg.
        :param kwargs: search parameters
        """
        return self._get(self._build_url(self.endpoint.search(*args, **kwargs)))

    # TODO: https://github.com/facetoe/zenpy/issues/123
    def _get_sla(self, sla_id):
        pass


class SlaPolicyApi(CRUDApi):
    def __init__(self, config):
        super(SlaPolicyApi, self).__init__(config, object_type='sla_policy')

    def create(self, api_objects, **kwargs):
        if isinstance(api_objects, collections.Iterable):
            raise ZenpyException("Cannot create multiple sla policies!")
        super(SlaPolicyApi, self).create(api_objects, **kwargs)

    def update(self, api_objects, **kwargs):
        if isinstance(api_objects, collections.Iterable):
            raise ZenpyException("Cannot update multiple sla policies!")
        super(SlaPolicyApi, self).update(api_objects, **kwargs)

    def definitions(self):
        url = self._build_url(self.endpoint.definitions())
        return self._get(url)


class ChatApiBase(Api):
    """
    Implements most generic ChatApi functionality. Most if the actual work is delegated to
    Request and Response handlers.
    """

    def __init__(self, config, endpoint, request_handler=None):
        super(ChatApiBase, self).__init__(config,
                                          object_type='chat',
                                          endpoint=endpoint)
        self._request_handler = request_handler or ChatApiRequest
        self._object_mapping = ChatObjectMapping(self)
        self._url_template = "%(protocol)s://www.zopim.com/%(api_prefix)s"
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
        return self._request_handler(self).perform("POST", *args, **kwargs)

    def update(self, *args, **kwargs):
        return self._request_handler(self).perform("PUT", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request_handler(self).perform("DELETE", *args, **kwargs)

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


class ChatApi(ChatApiBase):
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
