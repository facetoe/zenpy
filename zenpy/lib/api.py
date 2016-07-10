import json
from time import sleep

from zenpy.lib.endpoint import Endpoint
from zenpy.lib.exception import APIException, RecordNotFoundException
from zenpy.lib.generator import ResultGenerator
from zenpy.lib.manager import ApiObjectEncoder, ObjectManager
from zenpy.lib.util import to_snake_case

__author__ = 'facetoe'

from zenpy.lib.exception import ZenpyException
import logging

log = logging.getLogger(__name__)


class BaseApi(object):
    """
    Base class for API.
    """
    subdomain = None

    def __init__(self, subdomain, session):
        self.subdomain = subdomain
        self.protocol = 'https'
        self.version = 'v2'
        self.object_manager = ObjectManager(self)
        self.session = session

    def _post(self, url, payload):
        log.debug("POST: %s - %s" % (url, str(payload)))
        payload = json.loads(json.dumps(payload, cls=ApiObjectEncoder))
        response = self.session.post(url, json=payload)
        self._check_and_cache_response(response)
        return self._build_response(response.json())

    def _put(self, url, payload):
        payload = json.loads(json.dumps(payload, cls=ApiObjectEncoder))
        return self._call_api(self.session.put, url, json=payload)

    def _delete(self, url, payload=None):
        return self._call_api(self.session.delete, url, json=payload)

    def _get(self, url):
        return self._call_api(self.session.get, url)

    def _call_api(self, http_method, url, **kwargs):
        log.debug("{}: {}".format(http_method.__name__.upper(), url))
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
            response = http_method.get(url, **kwargs)
        return self._check_and_cache_response(response)

    def _get_items(self, endpoint, object_type, *args, **kwargs):
        sideload = 'sideload' not in kwargs or ('sideload' in kwargs and kwargs['sideload'])

        # If an ID is present a single object has been requested
        if 'id' in kwargs:
            return self._get_item(kwargs['id'], endpoint, object_type, sideload)

        if 'ids' in kwargs:
            cached_objects = []
            # Check to see if we have all objects in the cache.
            # If we are missing even one we need to request them all again.
            for _id in kwargs['ids']:
                obj = self.object_manager.query_cache(object_type, _id)
                if obj:
                    cached_objects.append(obj)
                else:
                    return self._get_paginated(endpoint, object_type, *args, **kwargs)
            return cached_objects

        return self._get_paginated(endpoint, object_type, *args, **kwargs)

    def _get_item(self, _id, endpoint, object_type, sideload=True, skip_cache=False):
        if not skip_cache:
            # Check if we already have this item in the cache
            item = self.object_manager.query_cache(object_type, _id)
            if item:
                return item

        _json = self._query(endpoint=endpoint(id=_id, sideload=sideload))

        # If the result is paginated return a generator
        if 'next_page' in _json:
            return ResultGenerator(self, object_type, _json)
        # Annoyingly, tags is always plural.
        if 'tags' in _json:
            return self.object_manager.object_from_json(object_type, _json[object_type + 's'])
        else:
            return self.object_manager.object_from_json(object_type, _json[object_type])

    def _get_paginated(self, endpoint, object_type, *args, **kwargs):
        _json = self._query(endpoint=endpoint(*args, **kwargs))
        return ResultGenerator(self, object_type, _json)

    def _query(self, endpoint):
        response = self._get(self._get_url(endpoint=endpoint))
        return response.json()

    def _build_response(self, response_json):
        # When updating and deleting API objects various responses can be returned
        # We can figure out what we have by the keys in the returned JSON
        if 'ticket' and 'audit' in response_json:
            return self.object_manager.object_from_json('ticket_audit', response_json)
        elif 'tags' in response_json:
            return response_json['tags']

        known_objects = ('ticket', 'user', 'job_status', 'group', 'satisfaction_rating', 'request', 'organization',
                         'organization_membership')

        for object_type in known_objects:
            if object_type in response_json:
                return self.object_manager.object_from_json(object_type, response_json[object_type])

        raise ZenpyException("Unknown Response: " + str(response_json))

    def _check_and_cache_response(self, response):
        if response.status_code > 299 or response.status_code < 200:
            # If it's just a RecordNotFound error raise the right exception,
            # otherwise try and get a nice error message.
            if 'application/json' in response.headers['content-type']:
                try:
                    _json = response.json()
                    if 'error' in _json and _json['error'] == 'RecordNotFound':
                        raise RecordNotFoundException(json.dumps(_json))
                    else:
                        raise APIException(json.dumps(_json))
                except ValueError:
                    pass

            # No can do, just raise the correct Exception.
            response.raise_for_status()
        else:
            try:
                self.object_manager.update_caches(response.json())
            except ValueError:
                pass
            return response

    def _get_url(self, endpoint=''):
        return "%(protocol)s://%(subdomain)s.zendesk.com/api/%(version)s/" % self.__dict__ + endpoint


class Api(BaseApi):
    """
    Add an Endpoint to direct the various operations to the correct API location.
    Also add an object_type to define the type of object this Api returns.

    Finally, add a whole bunch of convenience methods for the different object types.
    These methods line up with the ones generated by the gen_classes.py. Some of them
    simply return the parameter they were passed as the method will be deprecated or
    I haven't had a chance to implement it yet.
    """

    def __init__(self, subdomain, session, endpoint, object_type):
        BaseApi.__init__(self, subdomain, session)
        self.endpoint = endpoint
        self.object_type = object_type

    def __call__(self, *args, **kwargs):
        """
        Retrieve API objects. If called with no arguments returns a ResultGenerator of
        all retrievable items. Alternatively, can be called with an id to only return that item.
        """
        return self._get_items(self.endpoint, self.object_type, *args, **kwargs)

    def _get_user(self, _id, endpoint=Endpoint.users, object_type='user'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def _get_users(self, _ids, endpoint=Endpoint.users, object_type='user'):
        return self._get_items(endpoint, object_type, ids=_ids)

    def _get_comment(self, _id, endpoint=Endpoint.tickets.comments, object_type='comment'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def _get_organization(self, _id, endpoint=Endpoint.organizations, object_type='organization'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def _get_group(self, _id, endpoint=Endpoint.groups, object_type='group'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def _get_brand(self, _id, endpoint=Endpoint.brands, object_type='brand'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def _get_ticket(self, _id, endpoint=Endpoint.tickets, object_type='ticket', skip_cache=False):
        return self._get_item(_id, endpoint, object_type, sideload=False, skip_cache=skip_cache)

    def _get_events(self, events):
        for event in events:
            yield self.object_manager.object_from_json(event['type'].lower(), event)

    def _get_via(self, via):
        return self.object_manager.object_from_json('via', via)

    def _get_source(self, source):
        return self.object_manager.object_from_json('source', source)

    def _get_attachments(self, attachments):
        for attachment in attachments:
            yield self.object_manager.object_from_json('attachment', attachment)

    def _get_thumbnails(self, thumbnails):
        for thumbnail in thumbnails:
            yield self.object_manager.object_from_json('thumbnail', thumbnail)

    def _get_satisfaction_rating(self, satisfaction_rating):
        return self.object_manager.object_from_json('satisfaction_rating', satisfaction_rating)

    def _get_ticket_metric_item(self, metric_item):
        return self.object_manager.object_from_json('ticket_metric_item', metric_item)

    def _get_metadata(self, metadata):
        return self.object_manager.object_from_json('metadata', metadata)

    def _get_system(self, system):
        return self.object_manager.object_from_json('system', system)

    def _get_problem(self, problem_id):
        return self._get_item(problem_id, Endpoint.tickets, 'ticket')

    # This will be deprecated soon - https://developer.zendesk.com/rest_api/docs/web-portal/forums
    def _get_forum(self, forum_id):
        return forum_id

    def _get_user_fields(self, user_fields, endpoint=Endpoint().user_fields, object_type='user_field'):
        return self._get_fields(user_fields, endpoint, object_type)

    def _get_organization_fields(self, organization_fields, endpoint=Endpoint().organizations.organization_fields,
                                 object_type='organization_field'):
        return self._get_fields(organization_fields, endpoint, object_type)

    ## TODO implement this with Enterprise
    def _get_custom_fields(self, custom_fields):
        return custom_fields

    # This is ticket fields, hopefully it doesn't conflict with another field type
    def _get_fields(self, fields, object_type='ticket_field', endpoint=Endpoint().ticket_fields):
        if any([self.object_manager.query_cache(object_type, field) is None for field in [f['id'] for f in fields]]):
            # Populate field cache
            self._get(self._get_url(endpoint=endpoint()))
        for field in fields:
            yield self.object_manager.query_cache(object_type, field)


class ModifiableApi(Api):
    """
    ModifiableApi contains helper methods for modifying an API
    """

    def _get_type_and_payload(self, items):
        self._check_type(items)
        if isinstance(items, list):
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
        expected_class = self.object_manager.class_manager.class_for_type(self.object_type)
        if isinstance(items, list):
            if any((o.__class__ is not expected_class for o in items)):
                raise ZenpyException("Invalid type - expected %(expected_class)s" % locals())
        else:
            if items.__class__ is not expected_class:
                raise Exception("Invalid type - expected %(expected_class)s" % locals())

    def _do(self, action, endpoint_kwargs, payload=None, endpoint=None):
        if not endpoint:
            endpoint = self.endpoint
        url = self._get_url(endpoint=endpoint(**endpoint_kwargs))
        return action(url, payload=payload)


class CRUDApi(ModifiableApi):
    """
    CRUDApi supports create/update/delete operations
    """

    def create(self, api_objects):
        """
        Create (POST) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param api_objects: object or objects to create
        """
        object_type, payload = self._get_type_and_payload(api_objects)
        if object_type.endswith('s'):
            return self._do(self._post, dict(create_many=True, sideload=False), payload=payload)
        else:
            return self._do(self._post, dict(sideload=False), payload=payload)

    def update(self, items):
        """
        Update (PUT) one or more API objects. Before being submitted to Zendesk the object or objects
        will be serialized to JSON.

        :param api_objects: object or objects to update
        """
        object_type, payload = self._get_type_and_payload(items)
        if object_type.endswith('s'):
            return self._do(self._put, dict(update_many=True, sideload=False), payload=payload)
        else:
            return self._do(self._put, dict(id=items.id, sideload=False), payload=payload)

    def delete(self, items):
        """
        Delete (DELETE) one or more API objects. After successfully deleting the objects from the API
        they will also be removed from the relevant Zenpy caches.

        :param api_objects: object or objects to delete
        """
        object_type, payload = self._get_type_and_payload(items)
        if object_type.endswith('s'):
            response = self._do(self._delete, dict(destroy_ids=[i.id for i in items], sideload=False))
        else:
            response = self._do(self._delete, dict(id=items.id, sideload=False))
        self.object_manager.delete_from_cache(items)
        return response


class SuspendedTicketApi(ModifiableApi):
    """
    The SuspendedTicketApi adds some SuspendedTicket specific functionality
    """

    def __init__(self, subdomain, session, endpoint):
        Api.__init__(self, subdomain, session, endpoint=endpoint,
                     object_type='suspended_ticket')

    def recover(self, tickets):
        """
        Recover (PUT) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to recover
        """
        object_type, payload = self._get_type_and_payload(tickets)
        if object_type.endswith('s'):
            return self._do(self._put, dict(
                recover_ids=[i.id for i in tickets], sideload=False),
                            endpoint=self.endpoint, payload=payload)
        else:
            return self._do(self._put, dict(id=tickets.id, sideload=False),
                            endpoint=self.endpoint.recover,
                            payload=payload)

    def delete(self, tickets):
        """
        Delete (DELETE) one or more SuspendedTickets.

        :param tickets: one or more SuspendedTickets to delete
        """
        object_type, payload = self._get_type_and_payload(tickets)
        if object_type.endswith('s'):
            response = self._do(self._delete, dict(destroy_ids=[i.id for i in tickets], sideload=False))
        else:
            response = self._do(self._delete, dict(id=tickets.id, sideload=False))
        return response


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
                sideload=False)),
            payload={'tags': tags})

    def set_tags(self, id, tags):
        """
        Set (POST) one or more tags.

        :param id: the id of the object to tag
        :param tags: array of tags to apply to object
        """
        return self._post(self._get_url(
            endpoint=self.endpoint.tags(
                id=id,
                sideload=False)),
            payload={'tags': tags})

    def delete_tags(self, id, tags):
        """
        Delete (DELETE) one or more tags.

        :param id: the id of the object to delete tag from
        :param tags: array of tags to delete from object
        """
        return self._delete(self._get_url(
            endpoint=self.endpoint.tags(
                id=id,
                sideload=False, )),
            payload={'tags': tags})

    def tags(self, id):
        """
        Lists the most popular recent tags in decreasing popularity
        """
        return self._get_items(self.endpoint.tags, 'tag', id=id)


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
        return self._post(self._get_url(self.endpoint.satisfaction_ratings(
            id=id,
            sideload=False
        )),
            payload={'satisfaction_rating': vars(rating)})


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

    def __init__(self, subdomain, session, endpoint):
        Api.__init__(self, subdomain, session, endpoint=endpoint, object_type='user')

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
        return self._get_items(self.endpoint.assigned, 'ticket', user_id)

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

        :param user: User object or list of User objects
        :return: the created/updated User or a  JobStatus object if a list was passed
        """

        object_type, payload = self._get_type_and_payload(users)
        if object_type.endswith('s'):
            return self._do(self._post,
                            dict(create_or_update_many=True, sideload=False),
                            payload=payload,
                            endpoint=self.endpoint.create_or_update_many)
        else:
            return self._do(self._post,
                            dict(sideload=False),
                            payload=payload,
                            endpoint=self.endpoint.create_or_update)


class EndUserApi(CRUDApi):
    """
    EndUsers can only update.
    """

    def __init__(self, subdomain, session, endpoint):
        Api.__init__(self, subdomain, session, endpoint=endpoint, object_type='user')

    def delete(self, items):
        raise ZenpyException("EndUsers cannot delete!")

    def create(self, api_objects):
        raise ZenpyException("EndUsers cannot create!")


class OrganizationApi(TaggableApi, IncrementalApi, CRUDApi):
    def __init__(self, subdomain, session, endpoint):
        Api.__init__(self, subdomain, session, endpoint=endpoint,
                     object_type='organization')

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


class OrganizationMembershipApi(CRUDApi):
    """
    The OrganizationMembershipApi allows the creation and deletion of Organization Memberships
    """

    def __init__(self, subdomain, session, endpoint):
        Api.__init__(self, subdomain, session, endpoint=endpoint, object_type='organization_membership')

    def update(self, items):
        raise ZenpyException("You cannot update Organization Memberships!")


class TicketApi(RateableApi, TaggableApi, IncrementalApi, CRUDApi):
    """
    The TicketApi adds some Ticket specific functionality
    """

    def __init__(self, subdomain, session, endpoint):
        Api.__init__(self, subdomain, session, endpoint=endpoint, object_type='ticket')

    def organizations(self, org_id):
        """
        Retrieve the tickets for this organization.

        :param id: organization id
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

        :param id: ticket id
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
        :param id: ticket id
        """
        return self._get_items(self.endpoint.audits, 'ticket_audit', id=ticket_id)

    def metrics(self, ticket_id):
        """
        Retrieve TicketMetric.
        :param id: ticket id
        """
        return self._get_items(self.endpoint.metrics, 'ticket_metric', id=ticket_id)

    def metrics_incremental(self, start_time):
        """
        Retrieve TicketMetric incremental
        :param start_time: time to retrieve events from.
        """
        return self._get_items(self.endpoint.metrics.incremental, 'ticket_metric_events', start_time=start_time)


class TicketImportAPI(CRUDApi):
    def __init__(self, subdomain, session, endpoint):
        Api.__init__(self, subdomain, session, endpoint=endpoint, object_type='ticket')

    def __call__(self, *args, **kwargs):
        raise ZenpyException("You must pass ticket objects to this endpoint!")

    def update(self, items):
        raise ZenpyException("You cannot update objects using ticket_import endpoint!")

    def delete(self, items):
        raise ZenpyException("You cannot delete objets using the ticket_import endpoint!")


class RequestAPI(CRUDApi):
    def __init__(self, subdomain, session, endpoint):
        Api.__init__(self, subdomain, session, endpoint=endpoint, object_type='request')

    def open(self):
        """
        Return all open requests
        """
        return self._get_items(self.endpoint.open, 'request', sideload=False)

    def solved(self):
        """
        Return all solved requests
        """
        return self._get_items(self.endpoint.solved, 'request', sideload=False)

    def ccd(self):
        """
        Return all ccd requests
        """
        return self._get_items(self.endpoint.ccd, 'request', sideload=False)

    def comments(self, request_id):
        """
        Return comments for request
        """
        return self._get_items(self.endpoint.comments, 'comment', sideload=False, id=request_id)

    def delete(self, items):
        raise ZenpyException("You cannot delete requests!")

    def search(self, *args, **kwargs):
        """
        Search for requests. See the Zendesk docs for more information on the syntax - https://developer.zendesk.com/rest_api/docs/core/requests#searching-requests
        """
        return self._get_items(self.endpoint.search, 'request', *args, **kwargs)
