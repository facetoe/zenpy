from time import sleep

__author__ = 'facetoe'

from zenpy.lib.manager import ObjectManager, ApiObjectEncoder
from zenpy.lib.exception import ZenpyException, APIException, RecordNotFoundException
from zenpy.lib.endpoint import Endpoint
from zenpy.lib.generator import ResultGenerator

import json
import requests
import logging

log = logging.getLogger(__name__)


class BaseApi(object):
    """
    Base class for API.
    """
    email = None
    token = None
    password = None
    subdomain = None
    protocol = None
    version = None
    base_url = None

    headers = {'Content-type': 'application/json',
               'User-Agent': 'Zenpy/0.0.20'}

    def __init__(self, subdomain, email, token, password):
        self.email = email
        self.token = token
        self.password = password
        self.subdomain = subdomain
        self.protocol = 'https'
        self.version = 'v2'
        self.base_url = self._get_url()
        self.object_manager = ObjectManager(self)

    def _post(self, url, payload):
        log.debug("POST: " + url)
        payload = json.loads(json.dumps(payload, cls=ApiObjectEncoder))
        response = requests.post(url, auth=self._get_auth(), json=payload, headers=self.headers)
        self._check_and_cache_response(response)
        return self._build_response(response.json())

    def _put(self, url, payload):
        log.debug("PUT: " + url)
        payload = json.loads(json.dumps(payload, cls=ApiObjectEncoder))
        response = requests.put(url, auth=self._get_auth(), json=payload, headers=self.headers)
        self._check_and_cache_response(response)
        return self._build_response(response.json())

    def _delete(self, url, payload=None):
        log.debug("DELETE: " + url)
        if payload:
            response = requests.delete(url, auth=self._get_auth(), json=payload, headers=self.headers)
        else:
            response = requests.delete(url, auth=self._get_auth())
        return self._check_and_cache_response(response)

    def _get(self, url, stream=False):
        log.debug("GET: " + url)
        response = requests.get(url, auth=self._get_auth(), stream=stream)

        # If we are being rate-limited, wait the required period before trying again.
        while 'retry-after' in response.headers and int(response.headers['retry-after']) > 0:
            retry_after_seconds = int(response.headers['retry-after'])
            log.warn(
                "APIRateLimitExceeded - sleeping for requested retry-after period: %s seconds" % retry_after_seconds)
            while retry_after_seconds > 0:
                retry_after_seconds -= 1
                log.debug("APIRateLimitExceeded - sleeping: %s more seconds" % retry_after_seconds)
                sleep(1)
            response = requests.get(url, auth=self._get_auth(), stream=stream)
        return self._check_and_cache_response(response)

    def _get_items(self, endpoint, object_type, kwargs):
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
                    return self._get_paginated(endpoint, kwargs, object_type)
            return cached_objects

        return self._get_paginated(endpoint, kwargs, object_type)

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

    def _get_paginated(self, endpoint, kwargs, object_type):
        _json = self._query(endpoint=endpoint(**kwargs))
        return ResultGenerator(self, object_type, _json)

    def _query(self, endpoint):
        response = self._get(self._get_url(endpoint=endpoint))
        return response.json()

    def _build_response(self, response_json):
        # When updating and deleting API objects various responses can be returned
        # We can figure out what we have by the keys in the returned JSON
        if 'ticket' and 'audit' in response_json:
            response = self.object_manager.object_from_json('ticket_audit', response_json)
        elif 'ticket' in response_json:
            response = self.object_manager.object_from_json('ticket', response_json['ticket'])
        elif 'user' in response_json:
            response = self.object_manager.object_from_json('user', response_json['user'])
        elif 'job_status' in response_json:
            response = self.object_manager.object_from_json('job_status', response_json['job_status'])
        elif 'group' in response_json:
            response = self.object_manager.object_from_json('group', response_json['group'])
        elif 'organization' in response_json:
            response = self.object_manager.object_from_json('organization', response_json['organization'])
        elif 'tags' in response_json:
            return response_json['tags']
        elif 'satisfaction_rating' in response_json:
            return self.object_manager.object_from_json('satisfaction_rating', response_json['satisfaction_rating'])
        else:
            raise ZenpyException("Unknown Response: " + str(response_json))

        return response

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
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError, e:
                raise APIException(e.message)
        else:
            try:
                self.object_manager.update_caches(response.json())
            except ValueError:
                pass
            return response

    def _get_url(self, endpoint=''):
        return "%(protocol)s://%(subdomain)s.zendesk.com/api/%(version)s/" % self.__dict__ + endpoint

    def _get_auth(self):
        if self.password:
            return self.email, self.password
        else:
            return self.email + '/token', self.token


class Api(BaseApi):
    """
    Add an Endpoint to direct the various operations to the correct API location.
    Also add an object_type to define the type of object this Api returns.

    Finally, add a whole bunch of convenience methods for the different object types.
    These methods line up with the ones generated by the gen_classes.py. Some of them
    simply return the parameter they were passed as the method will be deprecated or
    I haven't had a chance to implement it yet.
    """

    def __init__(self, subdomain, email, password, token, endpoint, object_type):
        BaseApi.__init__(self, subdomain, email, token, password)
        self.endpoint = endpoint
        self.object_type = object_type

    def __call__(self, **kwargs):
        return self._get_items(self.endpoint, self.object_type, kwargs)

    def get_user(self, _id, endpoint=Endpoint().users, object_type='user'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def get_users(self, _ids, endpoint=Endpoint().users, object_type='user'):
        return self._get_items(endpoint, object_type, dict(ids=_ids))

    def get_comment(self, _id, endpoint=Endpoint().tickets.comments, object_type='comment'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def get_organization(self, _id, endpoint=Endpoint().organizations, object_type='organization'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def get_group(self, _id, endpoint=Endpoint().groups, object_type='group'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def get_brand(self, _id, endpoint=Endpoint().brands, object_type='brand'):
        return self._get_item(_id, endpoint, object_type, sideload=True)

    def get_ticket(self, _id, endpoint=Endpoint().tickets, object_type='ticket', skip_cache=False):
        return self._get_item(_id, endpoint, object_type, sideload=False, skip_cache=skip_cache)

    def get_events(self, events):
        for event in events:
            yield self.object_manager.object_from_json(event['type'].lower(), event)

    def get_via(self, via):
        return self.object_manager.object_from_json('via', via)

    def get_source(self, source):
        return self.object_manager.object_from_json('source', source)

    def get_attachment(self, attachment):
        return self.object_manager.object_from_json('attachment', attachment)

    def get_satisfaction_rating(self, satisfaction_rating):
        return self.object_manager.object_from_json('satisfaction_rating', satisfaction_rating)

    def get_ticket_metric_item(self, metric_item):
        return self.object_manager.object_from_json('ticket_metric_item', metric_item)

    def get_metadata(self, metadata):
        return self.object_manager.object_from_json('metadata', metadata)

    def get_system(self, system):
        return self.object_manager.object_from_json('system', system)

    # This will be deprecated soon - https://developer.zendesk.com/rest_api/docs/web-portal/forums
    def get_forum(self, forum_id):
        return forum_id

    def get_user_fields(self, user_fields, endpoint=Endpoint().users.user_fields, object_type='user_field'):
        return self._get_fields(user_fields, endpoint, object_type)

    def get_organization_fields(self, organization_fields, endpoint=Endpoint().organizations.organization_fields,
                                object_type='organization_field'):
        return self._get_fields(organization_fields, endpoint, object_type)

    ## TODO implement this with Enterprise
    def get_custom_fields(self, custom_fields):
        return custom_fields

    # This is ticket fields, hopefully it doesn't conflict with another field type
    def get_fields(self, fields, object_type='ticket_field', endpoint=Endpoint().ticket_fields):
        return self._get_fields([f['id'] for f in fields], endpoint, object_type)

    # Need to clean this up somehow.
    def _get_fields(self, fields, endpoint, object_type):
        if any([self.object_manager.query_cache(object_type, field) is None for field in fields]):
            # Populate field cache
            self._get(self._get_url(endpoint=endpoint()))
        for field in fields:
            yield self.object_manager.query_cache(object_type, field)


class ModifiableApi(Api):
    """
    ModifiableApi contains helper methods for modifying an API
    """

    def _get_type_and_payload(self, items):
        if isinstance(items, list):
            first_obj = next((x for x in items))
            # Object name needs to be plural when targeting many
            object_type = "%ss" % first_obj.__class__.__name__.lower()
            payload = {object_type: [json.loads(json.dumps(i, cls=ApiObjectEncoder)) for i in items]}
        else:
            object_type = items.__class__.__name__.lower()
            payload = {object_type: json.loads(json.dumps(items, cls=ApiObjectEncoder))}
        return object_type, payload

    def _do(self, action, endpoint_kwargs, payload=None, endpoint=None):
        if not endpoint:
            endpoint = self.endpoint
        return action(self._get_url(
            endpoint=endpoint(**endpoint_kwargs)),
            payload=payload)


class CRUDApi(ModifiableApi):
    """
    CRUDApi supports create/update/delete operations
    """

    def create(self, items):
        object_type, payload = self._get_type_and_payload(items)
        if object_type.endswith('s'):
            return self._do(self._post, dict(create_many=True, sideload=False), payload=payload)
        else:
            return self._do(self._post, dict(sideload=False), payload=payload)

    def update(self, items):
        object_type, payload = self._get_type_and_payload(items)
        if object_type.endswith('s'):
            return self._do(self._put, dict(update_many=True, sideload=False), payload=payload)
        else:
            return self._do(self._put, dict(id=items.id, sideload=False), payload=payload)

    def delete(self, items):
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

    def __init__(self, subdomain, email, token, password, endpoint):
        Api.__init__(self, subdomain, email, token=token, password=password, endpoint=endpoint,
                     object_type='suspended_ticket')

    def recover(self, items):
        object_type, payload = self._get_type_and_payload(items)
        if object_type.endswith('s'):
            return self._do(self._put, dict(
                recover_ids=[i.id for i in items], sideload=False),
                            endpoint=self.endpoint, payload=payload)
        else:
            return self._do(self._put, dict(id=items.id, sideload=False),
                            endpoint=self.endpoint.recover,
                            payload=payload)

    def delete(self, items):
        object_type, payload = self._get_type_and_payload(items)
        if object_type.endswith('s'):
            response = self._do(self._delete, dict(destroy_ids=[i.id for i in items], sideload=False))
        else:
            response = self._do(self._delete, dict(id=items.id, sideload=False))
        return response


class TaggableApi(Api):
    """
    TaggableApi supports getting, setting, adding and deleting tags.
    """

    def add_tags(self, id, tags):
        return self._put(self._get_url(
            endpoint=self.endpoint.tags(
                id=id,
                sideload=False)),
            payload={'tags': tags})

    def set_tags(self, id, tags):
        return self._post(self._get_url(
            endpoint=self.endpoint.tags(
                id=id,
                sideload=False)),
            payload={'tags': tags})

    def delete_tags(self, id, tags):
        return self._delete(self._get_url(
            endpoint=self.endpoint.tags(
                id=id,
                sideload=False, )),
            payload={'tags': tags})

    def tags(self, **kwargs):
        return self._get_items(self.endpoint.tags, 'tag', kwargs)


class RateableApi(Api):
    def rate(self, id, rating):
        return self._post(self._get_url(self.endpoint.satisfaction_ratings(
            id=id,
            sideload=False
        )),
            payload={'satisfaction_rating': vars(rating)})


class IncrementalApi(Api):
    """
    IncrementalApi supports the incremental endpoint.
    """

    def incremental(self, **kwargs):
        return self._get_items(self.endpoint.incremental, self.object_type, kwargs)


class UserApi(TaggableApi, IncrementalApi, CRUDApi):
    """
    The UserApi adds some User specific functionality
    """

    def __init__(self, subdomain, email, token, password, endpoint):
        Api.__init__(self, subdomain, email, token=token, password=password, endpoint=endpoint, object_type='user')

    def groups(self, **kwargs):
        return self._get_items(self.endpoint.groups, 'group', kwargs)

    def organizations(self, **kwargs):
        return self._get_items(self.endpoint.organizations, 'organization', kwargs)

    def requested(self, **kwargs):
        return self._get_items(self.endpoint.requested, 'ticket', kwargs)

    def cced(self, **kwargs):
        return self._get_items(self.endpoint.cced, 'ticket', kwargs)

    def assigned(self, **kwargs):
        return self._get_items(self.endpoint.assigned, 'ticket', kwargs)

    def group_memberships(self, **kwargs):
        return self._get_items(self.endpoint.group_memberships, 'group_membership', kwargs)

    def user_fields(self, **kwargs):
        return self._get_items(self.endpoint.user_fields, 'user_field', kwargs)


class EndUserApi(CRUDApi):
    """
    EndUsers can only update.
    """

    def __init__(self, subdomain, email, token, password, endpoint):
        Api.__init__(self, subdomain, email, token=token, password=password, endpoint=endpoint, object_type='user')

    def delete(self, items):
        raise ZenpyException("EndUsers cannot delete!")

    def create(self, items):
        raise ZenpyException("EndUsers cannot create!")


class OranizationApi(TaggableApi, IncrementalApi, CRUDApi):
    def __init__(self, subdomain, email, token, password, endpoint):
        Api.__init__(self, subdomain, email, token=token, password=password, endpoint=endpoint,
                     object_type='organization')

    def __call__(self, **kwargs):
        return self._get_items(self.endpoint, self.object_type, kwargs)

    def organization_fields(self, **kwargs):
        return self._get_items(self.endpoint.organization_fields, 'organization_field', kwargs)


class TicketApi(RateableApi, TaggableApi, IncrementalApi, CRUDApi):
    """
    The TicketApi adds some Ticket specific functionality
    """

    def __init__(self, subdomain, email, token, password, endpoint):
        Api.__init__(self, subdomain, email, token=token, password=password, endpoint=endpoint, object_type='ticket')

    def __call__(self, **kwargs):
        return self._get_items(self.endpoint, self.object_type, kwargs)

    def organizations(self, **kwargs):
        return self._get_items(self.endpoint.organizations, 'ticket', kwargs)

    def recent(self, **kwargs):
        return self._get_items(self.endpoint.recent, 'ticket', kwargs)

    def comments(self, **kwargs):
        return self._get_items(self.endpoint.comments, 'comment', kwargs)

    def events(self, **kwargs):
        return self._get_items(self.endpoint.events, 'ticket_event', kwargs)

    def audits(self, **kwargs):
        return self._get_items(self.endpoint.audits, 'ticket_audit', kwargs)

    def metrics(self, **kwargs):
        return self._get_items(self.endpoint.metrics, 'ticket_metric', kwargs)


class TicketImportAPI(CRUDApi):
    def __init__(self, subdomain, email, token, password, endpoint):
        Api.__init__(self, subdomain, email, token=token, password=password, endpoint=endpoint, object_type='ticket')

    def __call__(self, *args, **kwargs):
        raise ZenpyException("You must pass ticket objects to this endpoint!")

    def update(self, items):
        raise ZenpyException("You cannot update objects using ticket_import endpoint!")

    def delete(self, items):
        raise ZenpyException("You cannot delete objets using the ticket_import endpoint!")


class RequestAPI(CRUDApi):
    def __init__(self, subdomain, email, token, password, endpoint):
        Api.__init__(self, subdomain, email, token=token, password=password, endpoint=endpoint, object_type='request')
