import json
import logging

import os
from datetime import datetime, date
from json import JSONEncoder
from time import sleep, time

from zenpy.lib.api_objects import User, Ticket, Macro, Identity
from zenpy.lib.cache import query_cache, delete_from_cache
from zenpy.lib.endpoint import Endpoint
from zenpy.lib.exception import APIException, RecordNotFoundException
from zenpy.lib.exception import ZenpyException
from zenpy.lib.generator import ResultGenerator
from zenpy.lib.manager import class_for_type, object_from_json
from zenpy.lib.util import to_snake_case, is_iterable_but_not_string, as_singular

__author__ = 'facetoe'

log = logging.getLogger(__name__)


class ApiObjectEncoder(JSONEncoder):
    """ Class for encoding API objects"""

    def default(self, o):
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        elif isinstance(o, datetime):
            return o.date().isoformat()
        elif isinstance(o, date):
            return o.isoformat()


def serialize(api_object):
    return json.loads(json.dumps(api_object, cls=ApiObjectEncoder))


class BaseApi(object):
    """
    Base class for API.
    """
    KNOWN_RESPONSES = ('ticket',
                       'user',
                       'job_status',
                       'group',
                       'satisfaction_rating',
                       'request',
                       'organization',
                       'organization_membership',
                       'upload',
                       'result',
                       'identity')

    def __init__(self, subdomain, session, endpoint, object_type, timeout, ratelimit):
        self.subdomain = subdomain
        self.session = session
        self.timeout = timeout
        self.ratelimit = ratelimit
        self.endpoint = endpoint
        self.object_type = object_type
        self.protocol = 'https'
        self.version = 'v2'
        self.callsafety = {
            'lastcalltime': None,
            'lastlimitremaining': None
        }

    def _post(self, url, payload, data=None):
        headers = {'Content-Type': 'application/octet-stream'} if data else None
        response = self._call_api(self.session.post, url,
                                  json=serialize(payload),
                                  data=data,
                                  headers=headers,
                                  timeout=self.timeout)
        return response

    def _put(self, url, payload):
        return self._call_api(self.session.put, url, json=serialize(payload), timeout=self.timeout)

    def _delete(self, url, payload=None):
        return self._call_api(self.session.delete, url, json=payload, timeout=self.timeout)

    def _get(self, url):
        return self._call_api(self.session.get, url, timeout=self.timeout)

    def _call_api(self, http_method, url, **kwargs):
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
        self._update_callsafety(response)
        self._check_response(response)
        if http_method.__name__ == "delete":
            return response
        else:
            return self._deserialize(response.json())

    def _ratelimit(self, http_method, url, **kwargs):
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
                "Safety Limit Reached of %s remaining calls and time since last call is under 10 seconds" % self.ratelimit)
            while time_since_last_call() < 10:
                remaining_sleep = int(10 - time_since_last_call())
                log.debug("  -> sleeping: %s more seconds" % remaining_sleep)
                sleep(1)
            response = http_method(url, **kwargs)

        self.callsafety['lastcalltime'] = time()
        self.callsafety['lastlimitremaining'] = response.headers.get('X-Rate-Limit-Remaining', 0)
        return response

    def _update_callsafety(self, response):
        if self.ratelimit is not None:
            self.callsafety['lastcalltime'] = time()
            self.callsafety['lastlimitremaining'] = int(response.headers['X-Rate-Limit-Remaining'])

    def _deserialize(self, response_json):
        # TicketAudit and tags are special cases.
        if 'ticket' and 'audit' in response_json:
            return object_from_json(self, 'ticket_audit', response_json)
        elif 'tags' in response_json:
            return response_json['tags']

        # Search result
        if 'results' in response_json:
            return ResultGenerator(self, 'results', response_json)

        # A single object, eg "user"
        for object_type in self.KNOWN_RESPONSES:
            if object_type in response_json:
                return object_from_json(self, object_type, response_json[object_type])

        # Multiple of a single object, eg "users"
        for key in response_json:
            singular_key = as_singular(key)
            if singular_key in self.KNOWN_RESPONSES:
                return ResultGenerator(self, key, response_json)

        raise ZenpyException("Unknown Response: " + str(response_json))

    def _get_items(self, endpoint, object_type, *args, **kwargs):
        # If an ID is present a single object has been requested
        if 'id' in kwargs:
            return self._get_item(kwargs['id'], endpoint, object_type)

        if 'ids' in kwargs:
            cached_objects = []
            # Check to see if we have all objects in the cache.
            # If we are missing even one we need to request them all again.
            for _id in kwargs['ids']:
                obj = query_cache(object_type, _id)
                if obj:
                    cached_objects.append(obj)
                else:
                    return self._get(self._get_url(endpoint=endpoint(*args, **kwargs)))
            return cached_objects

        return self._get(self._get_url(endpoint=endpoint(*args, **kwargs)))

    def _get_item(self, _id, endpoint, object_type):
        # Check if we already have this item in the cache
        item = query_cache(object_type, _id)
        if item:
            return item
        return self._get(url=self._get_url(endpoint(id=_id)))

    def _check_response(self, response):
        if response.status_code > 299 or response.status_code < 200:
            log.debug("Received response code [%s] - headers: %s" % (response.status_code, str(response.headers)))
            # If it's just a RecordNotFound error raise the right exception,
            # otherwise try and get a nice error message.
            try:
                _json = response.json()
                if 'error' in _json and _json['error'] == 'RecordNotFound':
                    raise RecordNotFoundException(json.dumps(_json))
                else:
                    raise APIException(json.dumps(_json))
            except ValueError:
                response.raise_for_status()

    def _object_from_json(self, object_type, object_json):
        return self.object_manager.object_from_json(object_type, object_json)

    def _get_url(self, endpoint=''):
        return "%(protocol)s://%(subdomain)s.zendesk.com/api/%(version)s/" % self.__dict__ + endpoint


class Api(BaseApi):
    def __call__(self, *args, **kwargs):
        """
        Retrieve API objects. If called with no arguments returns a ResultGenerator of
        all retrievable items. Alternatively, can be called with an id to only return that item.
        """
        return self._get_items(self.endpoint, self.object_type, *args, **kwargs)

    def _get_user(self, _id):
        return self._get_item(_id, endpoint=Endpoint.users, object_type='user')

    def _get_users(self, _ids):
        return self._get_items(endpoint=Endpoint.users, object_type='user', ids=_ids)

    def _get_comment(self, _id):
        return self._get_item(_id, endpoint=Endpoint.tickets.comments, object_type='comment')

    def _get_organization(self, _id):
        return self._get_item(_id, endpoint=Endpoint.organizations, object_type='organization')

    def _get_group(self, _id):
        return self._get_item(_id, endpoint=Endpoint.groups, object_type='group')

    def _get_brand(self, _id):
        return self._get_item(_id, endpoint=Endpoint.brands, object_type='brand')

    def _get_ticket(self, _id):
        return self._get_item(_id, endpoint=Endpoint.tickets, object_type='ticket')

    def _get_actions(self, actions):
        for action in actions:
            yield self._object_from_json('action', action)

    def _get_events(self, events):
        for event in events:
            yield self._object_from_json(event['type'].lower(), event)

    def _get_via(self, via):
        return self._object_from_json('via', via)

    def _get_source(self, source):
        return self._object_from_json('source', source)

    def _get_attachments(self, attachments):
        for attachment in attachments:
            yield self._object_from_json('attachment', attachment)

    def _get_thumbnails(self, thumbnails):
        for thumbnail in thumbnails:
            yield self._object_from_json('thumbnail', thumbnail)

    def _get_satisfaction_rating(self, satisfaction_rating):
        return self._object_from_json('satisfaction_rating', satisfaction_rating)

    def _get_sharing_agreements(self, sharing_agreement_ids):
        sharing_agreements = []
        for _id in sharing_agreement_ids:
            sharing_agreement = self._get_item(_id, Endpoint.sharing_agreements, 'sharing_agreement')
            if sharing_agreement:
                sharing_agreements.append(sharing_agreement)
        return sharing_agreements

    def _get_ticket_metric_item(self, metric_item):
        return self._object_from_json('ticket_metric_item', metric_item)

    def _get_metadata(self, metadata):
        return self._object_from_json('metadata', metadata)

    def _get_system(self, system):
        return self._object_from_json('system', system)

    def _get_problem(self, problem_id):
        return self._get_item(problem_id, Endpoint.tickets, 'ticket')

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
        return self._object_from_json('upload', upload)

    def _get_attachment(self, attachment):
        return self._object_from_json('attachment', attachment)

    def _get_child_events(self, child_events):
        return child_events


class ModifiableApi(Api):
    """
    ModifiableApi contains helper methods for modifying an API
    """

    def _get_type_and_payload(self, items):
        self._check_type(items)
        if is_iterable_but_not_string(items):
            if len(items) < 1:
                raise ZenpyException("At least one item is required to perform this action!")
            first_obj = next((x for x in items))
            # Object name needs to be plural when targeting many
            object_type = "%ss" % to_snake_case(first_obj.__class__.__name__)
            payload = {object_type: [json.loads(json.dumps(i, cls=ApiObjectEncoder)) for i in items]}
        else:
            object_type = to_snake_case(items.__class__.__name__)
            payload = {object_type: json.loads(json.dumps(items, cls=ApiObjectEncoder))}
        return object_type, payload

    def _check_type(self, items):
        # We don't want people passing, for example, a Group object to a Ticket endpoint.
        expected_class = class_for_type(self.object_type)
        if is_iterable_but_not_string(items):
            if any((o.__class__ is not expected_class for o in items)):
                raise ZenpyException("Invalid type - expected %(expected_class)s" % locals())
        else:
            if items.__class__ is not expected_class:
                raise ZenpyException("Invalid type {} - expected {}".format(items.__class__, expected_class))

    def _do(self, action, endpoint_kwargs, endpoint_args=None, payload=None, endpoint=None):
        if not endpoint:
            endpoint = self.endpoint
        if not endpoint_args:
            endpoint_args = tuple()
        url = self._get_url(endpoint=endpoint(*endpoint_args, **endpoint_kwargs))
        return action(url, payload=payload)


class CRUDApi(ModifiableApi):
    """
    CRUDApi supports create/update/delete operations
    """

    # TODO - Fix the post method to be consistent with get and put.
    def create(self, api_objects):
        """
        Create (POST) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param api_objects: object or objects to create
        """
        object_type, payload = self._get_type_and_payload(api_objects)
        if object_type.endswith('s'):
            return self._do(self._post, dict(create_many=True), payload=payload)
        else:
            return self._do(self._post, dict(), payload=payload)

    def update(self, items):
        """
        Update (PUT) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param items: object or objects to update
        """
        object_type, payload = self._get_type_and_payload(items)
        if object_type.endswith('s'):
            response = self._do(self._put, dict(update_many=True), payload=payload)
        else:
            response = self._do(self._put, dict(id=items.id), payload=payload)
        return response

    def delete(self, items):
        """
        Delete (DELETE) one or more API objects. After successfully deleting the objects from the API
        they will also be removed from the relevant Zenpy caches.

        :param items: object or objects to delete
        """
        delete_from_cache(items)
        object_type, payload = self._get_type_and_payload(items)
        if object_type.endswith('s'):
            response = self._do(self._delete, dict(destroy_ids=[i.id for i in items]))
        else:
            response = self._do(self._delete, dict(id=items.id))
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
        object_type, payload = self._get_type_and_payload(tickets)
        if object_type.endswith('s'):
            return self._do(self._put, dict(
                recover_ids=[i.id for i in tickets]),
                            endpoint=self.endpoint, payload=payload)
        else:
            return self._do(self._put, dict(id=tickets.id),
                            endpoint=self.endpoint.recover,
                            payload=payload)

    def delete(self, tickets):
        """
        Delete (DELETE) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to delete
        """
        object_type, payload = self._get_type_and_payload(tickets)
        if object_type.endswith('s'):
            response = self._do(self._delete, dict(destroy_ids=[i.id for i in tickets]))
        else:
            response = self._do(self._delete, dict(id=tickets.id))
        return response


# noinspection PyShadowingBuiltins
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
        return self._put(self._get_url(
            endpoint=self.endpoint.tags(
                id=id,
            )),
            payload={'tags': tags})

    def set_tags(self, id, tags):
        """
        Set (POST) one or more tags.

        :param id: the id of the object to tag
        :param tags: array of tags to apply to object
        """
        return self._post(self._get_url(endpoint=self.endpoint.tags(id=id)), payload={'tags': tags})

    def delete_tags(self, id, tags):
        """
        Delete (DELETE) one or more tags.

        :param id: the id of the object to delete tag from
        :param tags: array of tags to delete from object
        """
        return self._delete(self._get_url(endpoint=self.endpoint.tags(id=id)), payload={'tags': tags})

    def tags(self, id):
        """
        Lists the most popular recent tags in decreasing popularity
        """
        return self._get_items(self.endpoint.tags, 'tag', id=id)


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
            self._get_url(self.endpoint.satisfaction_ratings(id=id)),
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
        return self._get_items(self.endpoint.incremental, self.object_type, start_time=start_time)


class UserApi(TaggableApi, IncrementalApi, CRUDApi):
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

            response = self._get(
                url=self._get_url(self.endpoint.show(user, identity))
            )
            return self._build_response(response.json())

        def create(self, user, identity):
            """
            Create an additional identity for the specified user
            
            :param user: User id or object
            :param identity: Identity object to be created
            :return: 
            """
            if not isinstance(identity, Identity):
                raise ZenpyException("You must pass an Identity object to this endpoint!")
            if isinstance(user, User):
                user = user.id
            object_type, payload = self._get_type_and_payload(identity)
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
            object_type, payload = self._get_type_and_payload(identity)
            response = self._do(self._put,
                                {},
                                endpoint=self.endpoint.update,
                                endpoint_args=(user, identity.id),
                                payload=payload)
            return self._build_response(response.json())

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
            response = self._do(self._put,
                                {},
                                endpoint=self.endpoint.make_primary,
                                endpoint_args=(user, identity))
            # We need to consume the generator here as we need to update the Identity cache.
            # If we don't then it is possible a stale version will be returned on a subsequent call.
            return [i for i in ResultGenerator(self, self.object_type, response.json())]

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
            response = self._do(self._put,
                                {},
                                endpoint=self.endpoint.verify,
                                endpoint_args=(user, identity))
            return self._build_response(response.json())

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
        return self._get_items(self.endpoint.groups, 'group', id=user_id)

    def organizations(self, user_id):
        """
        Retrieve the organizations for this user.

        :param user_id: user id
        """
        return self._get_items(self.endpoint.organizations, 'organization', id=user_id)

    def requested(self, user_id):
        """
        Retrieve the requested tickets for this user.

        :param user_id: user id
        """
        return self._get_items(self.endpoint.requested, 'ticket', id=user_id)

    def cced(self, user_id):
        """
        Retrieve the tickets this user is cc'd into.

        :param user_id: user id
        """
        return self._get_items(self.endpoint.cced, 'ticket', id=user_id)

    def assigned(self, user_id):
        """
        Retrieve the assigned tickets for this user.

        :param user_id: user id
        """
        return self._get_items(self.endpoint.assigned, 'ticket', id=user_id)

    def group_memberships(self, user_id):
        """
        Retrieve the group memberships for this user.

        :param user_id: user id
        """
        return self._get_items(self.endpoint.group_memberships, 'group_membership', id=user_id)

    def requests(self, **kwargs):
        return self._get_items(self.endpoint.requests, 'request', **kwargs)

    def related(self, user_id):
        """
        Returns the UserRelated information for the requested User

        :param user_id: User id
        :return: UserRelated
        """
        return self._get_items(self.endpoint.related, 'user_related', id=user_id)

    def me(self):
        """
        Return the logged in user
        """
        return self._get_item(None, self.endpoint.me, 'user')

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

        response = self._do(self._put,
                            endpoint_kwargs=dict(id=source_user),
                            payload=dict(user=dest_user),
                            endpoint=self.endpoint.merge)

        return self._build_response(response_json=response.json())

    def user_fields(self, user_id):
        """
        Retrieve the user fields for this user.

        :param user_id: user id
        """
        return self._get_items(self.endpoint.user_fields, 'user_field', id=user_id)

    def organization_memberships(self, user_id):
        """
        Retrieve the organization memberships for this user.

        :param user_id: user id
        """
        return self._get_items(self.endpoint.organization_memberships, 'organization_membership', id=user_id)

    def create_or_update(self, users):
        """
        Creates a user (POST) if the user does not already exist, or updates an existing user identified
        by e-mail address or external ID.

        :param users: User object or list of User objects
        :return: the created/updated User or a  JobStatus object if a list was passed
        """

        object_type, payload = self._get_type_and_payload(users)
        if object_type.endswith('s'):
            return self._do(self._post,
                            dict(create_or_update_many=True),
                            payload=payload,
                            endpoint=self.endpoint.create_or_update_many)
        else:
            return self._do(self._post,
                            dict(),
                            payload=payload,
                            endpoint=self.endpoint.create_or_update)


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

        return self._post(self._get_url(self.endpoint.upload(filename=target_name, token=token)),
                          data=fp,
                          payload={})


class EndUserApi(CRUDApi):
    """
    EndUsers can only update.
    """

    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='user', ratelimit=ratelimit)

    def delete(self, items):
        raise ZenpyException("EndUsers cannot delete!")

    def create(self, api_objects):
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
        return self._get_items(self.endpoint.organization_fields, 'organization_field', id=org_id)

    def organization_memberships(self, org_id):
        """
        Retrieve the organization fields for this organization.

        :param org_id: organization id
        """
        return self._get_items(self.endpoint.organization_memberships, 'organization_membership', id=org_id)

    def external(self, external_id):
        """
        Locate an Organization by it's external_id attribute.

        :param external_id: external id of organization
        """
        return self._get_items(self.endpoint.external, 'organization', id=external_id)

    def requests(self, **kwargs):
        return self._get_items(self.endpoint.requests, 'request', **kwargs)

    def create_or_update(self, organization):
        """
        Creates an organization if it doesn't already exist, or updates an existing
        organization identified by ID or external ID

        :param organization: Organization object
        :return: the created/updated Organization
        """

        object_type, payload = self._get_type_and_payload(organization)
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

    def update(self, items):
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

        self._check_type(satisfaction_rating)
        object_type, payload = self._get_type_and_payload(satisfaction_rating)
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

        return self._get_items(self.endpoint.apply, 'result', id=macro_id)


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
        return self._get_items(self.endpoint.organizations, 'ticket', id=org_id)

    def recent(self):
        """
        Retrieve the most recent tickets
        """
        return self._get_items(self.endpoint.recent, 'ticket', id=None)

    def comments(self, ticket_id):
        """
        Retrieve the comments for a ticket.

        :param ticket_id: ticket id
        """
        return self._get_items(self.endpoint.comments, 'comment', id=ticket_id)

    def events(self, start_time):
        """
        Retrieve TicketEvents
        :param start_time: time to retrieve events from.
        """
        return self._get_items(self.endpoint.events, 'ticket_event', start_time=start_time)

    def audits(self, ticket_id):
        """
        Retrieve TicketAudits.
        :param ticket_id: ticket id
        """
        return self._get_items(self.endpoint.audits, 'ticket_audit', id=ticket_id)

    def metrics(self, ticket_id):
        """
        Retrieve TicketMetric.
        :param ticket_id: ticket id
        """
        return self._get_items(self.endpoint.metrics, 'ticket_metric', id=ticket_id)

    def metrics_incremental(self, start_time):
        """
        Retrieve TicketMetric incremental
        :param start_time: time to retrieve events from.
        """
        return self._get_items(self.endpoint.metrics.incremental, 'ticket_metric_events', start_time=start_time)

    def show_macro_effect(self, ticket, macro):
        """
        Apply macro to ticket. Returns what it *would* do, does not alter the ticket.

        :param ticket: Ticket or ticket id to target
        :param macro_id: Macro or macro id to use
        """

        if isinstance(ticket, Ticket):
            ticket = ticket.id
        if isinstance(macro, Macro):
            macro = macro.id

        response = self._get(
            url=self._get_url(self.endpoint.macro(ticket, macro))
        )
        self._check_response(response)
        return self._build_response(response.json())

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

    def update(self, items):
        raise ZenpyException("You cannot update objects using ticket_import endpoint!")

    def delete(self, items):
        raise ZenpyException("You cannot delete objects using the ticket_import endpoint!")


class RequestAPI(CRUDApi):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='request', ratelimit=ratelimit)

    def open(self):
        """
        Return all open requests
        """
        return self._get_items(self.endpoint.open, 'request')

    def solved(self):
        """
        Return all solved requests
        """
        return self._get_items(self.endpoint.solved, 'request')

    def ccd(self):
        """
        Return all ccd requests
        """
        return self._get_items(self.endpoint.ccd, 'request')

    def comments(self, request_id):
        """
        Return comments for request
        """
        return self._get_items(self.endpoint.comments, 'comment', id=request_id)

    def delete(self, items):
        raise ZenpyException("You cannot delete requests!")

    def search(self, *args, **kwargs):
        """
        Search for requests. See the Zendesk docs for more information on the syntax
         https://developer.zendesk.com/rest_api/docs/core/requests#searching-requests
        """
        return self._get_items(self.endpoint.search, 'request', *args, **kwargs)


class SharingAgreementAPI(CRUDApi):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        Api.__init__(self, subdomain, session, endpoint, timeout=timeout, object_type='sharing_agreement',
                     ratelimit=ratelimit)
