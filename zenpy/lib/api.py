import collections
import json
import logging

import os
from datetime import datetime, date
from json import JSONEncoder
from time import sleep, time

from zenpy.lib.api_objects import User, Ticket, Macro, Identity
from zenpy.lib.cache import query_cache, delete_from_cache
from zenpy.lib.endpoint import Endpoint
from zenpy.lib.exception import APIException, RecordNotFoundException, TooManyValuesException
from zenpy.lib.exception import ZenpyException
from zenpy.lib.generator import SearchResultGenerator, ResultGenerator
from zenpy.lib.object_manager import class_for_type, object_from_json, CLASS_MAPPING
from zenpy.lib.util import is_iterable_but_not_string, as_plural, as_singular

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

    KNOWN_OBJECTS = CLASS_MAPPING.keys()

    def __init__(self, subdomain, session, endpoint, object_type, timeout, ratelimit):
        self.subdomain = subdomain
        self.session = session
        self.timeout = timeout
        self.ratelimit = ratelimit
        self.endpoint = endpoint
        self.object_type = object_type
        self.protocol = 'https'
        self.version = 'v2'
        self.base_url = "%(protocol)s://%(subdomain)s.zendesk.com/api/%(version)s" % vars(self)
        self.callsafety = {
            'lastcalltime': None,
            'lastlimitremaining': None
        }

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
        return self._call_api(self.session.delete, url, json=payload, timeout=self.timeout)

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
        while 'retry-after' in response.headers and int(response.headers['retry-after']) > 0:
            retry_after_seconds = int(response.headers['retry-after'])
            log.warn(
                "Waiting for requested retry-after period: %s seconds" % retry_after_seconds)
            while retry_after_seconds > 0:
                retry_after_seconds -= 1
                log.debug("    -> sleeping: %s more seconds" % retry_after_seconds)
                sleep(1)
            response = http_method(url, **kwargs)

        self._check_response(response)
        self._update_callsafety(response)
        return response

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
            self.callsafety['lastlimitremaining'] = int(response.headers['X-Rate-Limit-Remaining'])

    def _process_response(self, response):
        """
        Deserialize the returned objects and return either a single Zenpy object, or a ResultGenerator in 
        the case of multiple results. 

        This is complicated by the fact that when we receive a response from Zendesk, we don't really know 
        what the call was that initiated it. Through a series of guesses and a sprinkling of luck, try to
        return the correct response. The ordering of the statements in this method is highly important,
        changing it is likely to break things. 

        :param response: the requests Response object.
        """
        response_json = response.json()

        # Search result
        if 'results' in response_json:
            return SearchResultGenerator(self, response_json)

        # JobStatus responses also include a ticket key so treat it specially.
        zenpy_objects = self._deserialize(response_json)
        if 'job_status' in response_json:
            return zenpy_objects['job_status']

        # TicketAudit responses are another special case containing both
        # a ticket and audit key.
        if 'ticket' and 'audit' in response_json:
            return zenpy_objects['ticket_audit']

        # Collection of objects (eg, users/tickets)
        plural_object_type = as_plural(self.object_type)
        if plural_object_type in response_json:
            return ResultGenerator(self, response_json,
                                   object_type=plural_object_type,
                                   zenpy_objects=zenpy_objects[plural_object_type])

        # Here the response matches the API object_type, seems legit.
        if self.object_type in response_json:
            return zenpy_objects[self.object_type]

        # Could be anything, if we know of this object then return it.
        for zenpy_object_name in self.KNOWN_OBJECTS:
            if zenpy_object_name in response_json:
                return zenpy_objects[zenpy_object_name]

        # Maybe a collection of known objects?
        for zenpy_object_name in self.KNOWN_OBJECTS:
            plural_zenpy_object_name = as_plural(zenpy_object_name)
            if plural_zenpy_object_name in response_json:
                return ResultGenerator(self, response_json,
                                       object_type=plural_zenpy_object_name,
                                       zenpy_objects=zenpy_objects[plural_zenpy_object_name])

        # Bummer, bail out with an informative message.
        raise ZenpyException("Unknown Response: " + str(response_json))

    def _serialize(self, zenpy_object):
        """ Serialize a Zenpy object to JSON """
        return json.loads(json.dumps(zenpy_object, cls=ZenpyObjectEncoder))

    def _deserialize(self, response_json):
        """
        Locate and deserialize all objects in the returned JSON. 
        
        Return a dict keyed by object_type. If the key is plural, the value will be a list,
        if it is singular, the value will be an object of that type. 
        :param response_json: 
        """
        response_objects = dict()

        if all((t in response_json for t in ('ticket', 'audit'))):
            response_objects["ticket_audit"] = object_from_json(self, "ticket_audit", response_json)

        # Locate and store the single objects.
        for zenpy_object_name in self.KNOWN_OBJECTS:
            if zenpy_object_name in response_json:
                zenpy_object = object_from_json(self, zenpy_object_name, response_json[zenpy_object_name])
                response_objects[zenpy_object_name] = zenpy_object

        # Locate and store the collections of objects.
        for key, value in response_json.items():
            if isinstance(value, list):
                zenpy_object_name = as_singular(key)
                if zenpy_object_name in self.KNOWN_OBJECTS:
                    response_objects[key] = []
                    for object_json in response_json[key]:
                        zenpy_object = object_from_json(self, zenpy_object_name, object_json)
                        response_objects[key].append(zenpy_object)
        return response_objects

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
                    raise RecordNotFoundException(json.dumps(_json))
                elif err_type == "TooManyValues":
                    raise TooManyValuesException(json.dumps(_json))
                else:
                    raise APIException(json.dumps(_json))
            except ValueError:
                response.raise_for_status()

    def _build_url(self, endpoint=''):
        """ Build complete URL """
        return "/".join((self.base_url, endpoint))


class Api(BaseApi):
    """
    Most general API class. It is callable, and is suitable for basic API endpoints that can
    only be called with no arguments to return a collection, or an id to return a single item.

    This class also contains many methods for retrieving specific objects or collections of objects.
    These methods are called by the classes found in zenpy.lib.api_objects.
    """

    def __call__(self, *args, **kwargs):
        return self._query_zendesk(self.endpoint, self.object_type, *args, **kwargs)

    def _get_user(self, user_id):
        return self._query_zendesk(Endpoint.users, 'user', id=user_id)

    def _get_users(self, user_ids):
        return self._query_zendesk(endpoint=Endpoint.users, object_type='user', ids=user_ids)

    def _get_comment(self, comment_id):
        return self._query_zendesk(endpoint=Endpoint.tickets.comments, object_type='comment', id=comment_id)

    def _get_organization(self, organization_id):
        return self._query_zendesk(endpoint=Endpoint.organizations, object_type='organization', id=organization_id)

    def _get_group(self, group_id):
        return self._query_zendesk(endpoint=Endpoint.groups, object_type='group', id=group_id)

    def _get_brand(self, brand_id):
        return self._query_zendesk(endpoint=Endpoint.brands, object_type='brand', id=brand_id)

    def _get_ticket(self, ticket_id):
        return self._query_zendesk(endpoint=Endpoint.tickets, object_type='ticket', id=ticket_id)

    def _get_actions(self, actions):
        for action in actions:
            yield object_from_json(self, 'action', action)

    def _get_events(self, events):
        for event in events:
            yield object_from_json(self, event['type'].lower(), event)

    def _get_via(self, via):
        return object_from_json(self, 'via', via)

    def _get_source(self, source):
        return object_from_json(self, 'source', source)

    def _get_attachments(self, attachments):
        for attachment in attachments:
            yield object_from_json(self, 'attachment', attachment)

    def _get_thumbnails(self, thumbnails):
        for thumbnail in thumbnails:
            yield object_from_json(self, 'thumbnail', thumbnail)

    def _get_satisfaction_rating(self, satisfaction_rating):
        return object_from_json(self, 'satisfaction_rating', satisfaction_rating)

    def _get_sharing_agreements(self, sharing_agreement_ids):
        sharing_agreements = []
        for _id in sharing_agreement_ids:
            sharing_agreement = self._query_zendesk(endpoint=Endpoint.sharing_agreements,
                                                    object_type='sharing_agreement',
                                                    id=_id)
            if sharing_agreement:
                sharing_agreements.append(sharing_agreement)
        return sharing_agreements

    def _get_ticket_metric_item(self, metric_item):
        return object_from_json(self, 'ticket_metric_item', metric_item)

    def _get_metadata(self, metadata):
        return object_from_json(self, 'metadata', metadata)

    def _get_system(self, system):
        return object_from_json(self, 'system', system)

    def _get_problem(self, problem_id):
        return self._query_zendesk(Endpoint.tickets, 'ticket', id=problem_id)

    # This will be deprecated soon - https://developer.zendesk.com/rest_api/docs/web-portal/forums
    def _get_forum(self, forum_id):
        return forum_id

    def _get_user_fields(self, user_fields):
        return user_fields

    def _get_organization_fields(self, organization_fields):
        return organization_fields

    # TODO implement this with Enterprise
    def _get_custom_fields(self, custom_fields):
        return custom_fields

    # This is ticket fields, hopefully it doesn't conflict with another field type
    def _get_fields(self, fields):
        return fields

    def _get_upload(self, upload):
        return object_from_json(self, 'upload', upload)

    def _get_attachment(self, attachment):
        return object_from_json(self, 'attachment', attachment)

    def _get_child_events(self, child_events):
        return child_events

    # JobStatus results
    def _get_results(self, results):
        return results


class ModifiableApi(Api):
    """
    ModifiableApi contains helper methods for modifying an API
    """

    def _build_payload(self, api_objects):
        self._check_type(api_objects)
        if isinstance(api_objects, collections.Iterable):
            payload_key = as_plural(self.object_type)
        else:
            payload_key = self.object_type
        return {payload_key: json.loads(json.dumps(api_objects, cls=ZenpyObjectEncoder))}

    def _check_type(self, zenpy_objects):
        """ Ensure the passed type matches this API's object_type. """
        expected_type = class_for_type(self.object_type)
        if not is_iterable_but_not_string(zenpy_objects):
            zenpy_objects = [zenpy_objects]
        for zenpy_object in zenpy_objects:
            if type(zenpy_object) is not expected_type:
                raise ZenpyException(
                    "Invalid type - expected {} found {}".format(expected_type, type(zenpy_object))
                )

    def _do(self, action, endpoint_kwargs, endpoint_args=None, endpoint=None, **kwargs):
        if not endpoint:
            endpoint = self.endpoint
        if not endpoint_args:
            endpoint_args = tuple()
        url = self._build_url(endpoint=endpoint(*endpoint_args, **endpoint_kwargs))
        return action(url, **kwargs)


class CRUDApi(ModifiableApi):
    """
    CRUDApi supports create/update/delete operations
    """

    def create(self, api_objects, **kwargs):
        """
        Create (POST) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param api_objects: object or objects to create
        """
        payload = self._build_payload(api_objects)
        if isinstance(api_objects, collections.Iterable):
            kwargs['create_many'] = True
        return self._do(self._post, kwargs, payload=payload)

    def update(self, api_objects, **kwargs):
        """
        Update (PUT) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param api_objects: object or objects to update
        """
        payload = self._build_payload(api_objects)
        if isinstance(api_objects, collections.Iterable):
            kwargs['update_many'] = True
        else:
            kwargs['id'] = api_objects.id
        return self._do(self._put, kwargs, payload=payload)

    def delete(self, api_objects, **kwargs):
        """
        Delete (DELETE) one or more API objects. After successfully deleting the objects from the API
        they will also be removed from the relevant Zenpy caches.

        :param api_objects: object or objects to delete
        """
        payload = self._build_payload(api_objects)
        if isinstance(api_objects, collections.Iterable):
            kwargs['destroy_ids'] = [i.id for i in api_objects]
        else:
            kwargs['id'] = api_objects.id
        response = self._do(self._delete, kwargs, payload=payload)
        delete_from_cache(api_objects)
        return response


class SuspendedTicketApi(ModifiableApi):
    """
    The SuspendedTicketApi adds some SuspendedTicket specific functionality
    """

    def recover(self, tickets):
        """
        Recover (PUT) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to recover
        """
        payload = self._build_payload(tickets)
        endpoint_kwargs = dict()
        if isinstance(tickets, collections.Iterable):
            endpoint_kwargs['recover_ids'] = [i.id for i in tickets]
            endpoint = self.endpoint
        else:
            endpoint_kwargs['id'] = tickets.id
            endpoint = self.endpoint.recover
        return self._do(self._put, endpoint_kwargs, endpoint=endpoint, payload=payload)

    def delete(self, tickets):
        """
        Delete (DELETE) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to delete
        """
        endpoint_kwargs = dict()
        if isinstance(tickets, collections.Iterable):
            endpoint_kwargs['destroy_ids'] = [i.id for i in tickets]
        else:
            endpoint_kwargs['id'] = tickets.id
        payload = self._build_payload(tickets)
        response = self._do(self._delete, endpoint_kwargs, payload=payload)
        delete_from_cache(tickets)
        return response


class TaggableApi(Api):
    """
    TaggableApi supports getting, setting, adding and deleting tags.
    """

    def add_tags(self, _id, tags):
        """
        Add (PUT) one or more tags.

        :param _id: the id of the object to tag
        :param tags: array of tags to apply to object
        """
        return self._put(self._build_url(
            endpoint=self.endpoint.tags(
                id=_id,
            )),
            payload={'tags': tags})

    def set_tags(self, _id, tags):
        """
        Set (POST) one or more tags.

        :param _id: the id of the object to tag
        :param tags: array of tags to apply to object
        """
        return self._post(self._build_url(endpoint=self.endpoint.tags(id=_id)), payload={'tags': tags})

    def delete_tags(self, _id, tags):
        """
        Delete (DELETE) one or more tags.

        :param _id: the id of the object to delete tag from
        :param tags: array of tags to delete from object
        """
        return self._delete(self._build_url(endpoint=self.endpoint.tags(id=_id)), payload={'tags': tags})

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
        return self._post(
            self._build_url(self.endpoint.satisfaction_ratings(id=id)),
            payload={'satisfaction_rating': vars(rating)}
        )


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


class UserApi(IncrementalApi, CRUDApi):
    """
    The UserApi adds some User specific functionality
    """

    class UserIdentityApi(ModifiableApi):
        def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
            Api.__init__(self, subdomain, session, endpoint.identities,
                         object_type='identity',
                         timeout=timeout,
                         ratelimit=ratelimit)

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

            return self._do(self._get,
                            endpoint_kwargs={},
                            endpoint_args=(user, identity),
                            endpoint=self.endpoint.show)

        def create(self, user, identity):
            """
            Create an additional identity for the specified user

            :param user: User id or object
            :param identity: Identity object to be created
            """
            if not isinstance(identity, Identity):
                raise ZenpyException("You must pass an Identity object to this endpoint!")
            if isinstance(user, User):
                user = user.id
            payload = self._build_payload(identity)
            return self._do(self._post, dict(id=user), payload=payload)

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
            payload = self._build_payload(identity)
            return self._do(self._put,
                            endpoint_kwargs=dict(),
                            endpoint=self.endpoint.update,
                            endpoint_args=(user, identity.id),
                            payload=payload)

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
            return self._do(self._put,
                            endpoint_kwargs={},
                            endpoint_args=(user, identity),
                            endpoint=self.endpoint.make_primary)

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
            return self._do(self._put,
                            {},
                            endpoint=self.endpoint.request_verification,
                            endpoint_args=(user, identity))

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
            return self._do(self._put,
                            {},
                            endpoint=self.endpoint.verify,
                            endpoint_args=(user, identity))

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
            return self._do(self._delete,
                            {},
                            endpoint=self.endpoint.delete,
                            endpoint_args=(user, identity))

    identities = UserIdentityApi

    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, object_type='user', timeout=timeout, ratelimit=ratelimit)
        self.identities = self.identities(subdomain, session, endpoint, timeout=timeout, ratelimit=ratelimit)

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
        if isinstance(source_user, User):
            source_user = source_user.id
        if isinstance(dest_user, User):
            dest_user = dict(id=dest_user.id)
        else:
            dest_user = dict(id=dest_user)
        return self._do(self._put,
                        endpoint_kwargs=dict(id=source_user),
                        payload=dict(user=dest_user),
                        endpoint=self.endpoint.merge)

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

        payload = self._build_payload(users)
        endpoint_kwargs = dict()
        if isinstance(users, collections.Iterable):
            endpoint_kwargs['create_or_update_many'] = True
        return self._do(self._post, endpoint_kwargs, payload=payload,
                        endpoint=self.endpoint.create_or_update_many)


class AttachmentApi(Api):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, object_type='attachment', timeout=timeout, ratelimit=ratelimit)

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

        if hasattr(fp, 'read'):
            # File-like objects such as:
            #   PY3: io.StringIO, io.TextIOBase, io.BufferedIOBase
            #   PY2: file, io.StringIO, StringIO.StringIO, cStringIO.StringIO

            if not hasattr(fp, 'name') and not target_name:
                raise ZenpyException("upload requires a target file name")
            else:
                target_name = target_name or fp.name

        elif isinstance(fp, str):
            if os.path.isfile(fp):
                fp = open(fp, 'rb')
                target_name = target_name or fp.name
            elif not target_name:
                # Valid string, which is not a path, and without a target name
                raise ZenpyException("upload requires a target file name")

        elif not target_name:
            # Other serializable types accepted by requests (like dict)
            raise ZenpyException("upload requires a target file name")

        return self._post(self._build_url(self.endpoint.upload(filename=target_name, token=token)),
                          data=fp,
                          payload={})


class EndUserApi(CRUDApi):
    """
    EndUsers can only update.
    """

    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='user', ratelimit=ratelimit)

    def delete(self, api_objects, **kwargs):
        raise ZenpyException("EndUsers cannot delete!")

    def create(self, api_objects, **kwargs):
        raise ZenpyException("EndUsers cannot create!")


class OrganizationApi(TaggableApi, IncrementalApi, CRUDApi):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='organization',
                     ratelimit=ratelimit)

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

        object_type, payload = self._build_payload(organization)
        return self._do(self._post,
                        dict(),
                        payload=payload,
                        endpoint=self.endpoint.create_or_update)


class OrganizationMembershipApi(CRUDApi):
    """
    The OrganizationMembershipApi allows the creation and deletion of Organization Memberships
    """

    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='organization_membership',
                     ratelimit=ratelimit)

    def update(self, items, **kwargs):
        raise ZenpyException("You cannot update Organization Memberships!")


class SatisfactionRatingApi(ModifiableApi):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='satisfaction_rating',
                     ratelimit=ratelimit)

    def create(self, ticket_id, satisfaction_rating):
        """
        Create/update a Satisfaction Rating for a ticket.

        :param ticket_id: id of Ticket to rate
        :param satisfaction_rating: SatisfactionRating object.
        """

        payload = self._build_payload(satisfaction_rating)
        return self._do(self._post,
                        payload=payload,
                        endpoint=Endpoint.satisfaction_ratings.create,
                        endpoint_kwargs=dict(id=ticket_id))


class MacroApi(CRUDApi):
    def __init__(self, subdomain, session, timeout, ratelimit):
        Api.__init__(self, subdomain, session, Endpoint.macros, timeout=timeout, object_type='macro',
                     ratelimit=ratelimit)

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

    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='ticket', ratelimit=ratelimit)

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

        return self._do(self._get,
                        endpoint_kwargs={},
                        endpoint_args=(ticket, macro),
                        endpoint=self.endpoint.macro)

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
        if isinstance(target, Ticket):
            target = target.id
        if isinstance(source, Ticket):
            source_ids = [source.id]
        else:
            source_ids = [t.id if isinstance(t, Ticket) else t for t in source]

        payload = dict(
            ids=source_ids,
            target_comment=target_comment,
            source_comment=source_comment
        )

        return self._do(self._post,
                        endpoint_kwargs=dict(id=target),
                        payload=payload,
                        endpoint=self.endpoint.merge)


class TicketImportAPI(CRUDApi):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='ticket', ratelimit=ratelimit)

    def __call__(self, *args, **kwargs):
        raise ZenpyException("You must pass ticket objects to this endpoint!")

    def update(self, items, **kwargs):
        raise ZenpyException("You cannot update objects using ticket_import endpoint!")

    def delete(self, api_objects, **kwargs):
        raise ZenpyException("You cannot delete objects using the ticket_import endpoint!")


class RequestAPI(CRUDApi):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='request', ratelimit=ratelimit)

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
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint,
                     timeout=timeout,
                     object_type='sharing_agreement',
                     ratelimit=ratelimit)


class GroupApi(CRUDApi):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint,
                     timeout=timeout,
                     object_type='group',
                     ratelimit=ratelimit)
