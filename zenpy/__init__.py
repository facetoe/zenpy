import logging
import sys

import requests

from zenpy.lib.api import UserApi, Api, TicketApi, OranizationApi, SuspendedTicketApi, EndUserApi, TicketImportAPI, \
    RequestAPI
from zenpy.lib.cache import ZenpyCache
from zenpy.lib.endpoint import Endpoint
from zenpy.lib.exception import ZenpyException

log = logging.getLogger()
log.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
logging.getLogger("requests").setLevel(logging.WARNING)

__author__ = 'facetoe'


class Zenpy(object):
    """
    """

    headers = {'Content-type': 'application/json',
               'User-Agent': 'Zenpy/1.0.1'}

    def __init__(self, subdomain, email=None, token=None, password=None, debug=False, session=None):

        if debug:
            log.setLevel(logging.DEBUG)

        session = self._init_session(email, token, password, session)
        endpoint = Endpoint()

        self.users = UserApi(
            subdomain,
            session=session,
            endpoint=endpoint.users)

        self.groups = Api(
            subdomain,
            session=session,
            endpoint=endpoint.groups,
            object_type='group')

        self.organizations = OranizationApi(
            subdomain,
            session=session,
            endpoint=endpoint.organizations)

        self.tickets = TicketApi(
            subdomain,
            session=session,
            endpoint=endpoint.tickets)

        self.suspended_tickets = SuspendedTicketApi(
            subdomain,
            session=session,
            endpoint=endpoint.suspended_tickets)

        self.search = Api(
            subdomain,
            session=session,
            endpoint=endpoint.search,
            object_type='results')

        self.topics = Api(
            subdomain,
            session=session,
            endpoint=endpoint.topics,
            object_type='topic')

        self.attachments = Api(
            subdomain,
            session=session,
            endpoint=endpoint.attachments,
            object_type='attachment')

        self.brands = Api(
            subdomain,
            session=session,
            endpoint=endpoint.brands,
            object_type='brand')

        self.job_status = Api(
            subdomain,
            session=session,
            endpoint=endpoint.job_statuses,
            object_type='job_status')

        self.tags = Api(
            subdomain,
            session=session,
            endpoint=endpoint.tags,
            object_type='tag')

        self.satisfaction_ratings = Api(
            subdomain,
            session=session,
            endpoint=endpoint.satisfaction_ratings,
            object_type='satisfaction_rating'
        )

        self.activities = Api(
            subdomain,
            session=session,

            endpoint=endpoint.activities,
            object_type='activity'
        )

        self.group_memberships = Api(
            subdomain,
            session=session,
            endpoint=endpoint.group_memberships,
            object_type='group_membership'
        )

        self.end_user = EndUserApi(
            subdomain,
            session=session,
            endpoint=endpoint.end_user
        )

        self.ticket_metrics = Api(
            subdomain,
            session=session,
            endpoint=endpoint.ticket_metrics,
            object_type='ticket_metric'
        )

        self.ticket_fields = Api(
            subdomain,
            session=session,
            endpoint=endpoint.ticket_fields,
            object_type='ticket_field'
        )

        self.ticket_import = TicketImportAPI(
            subdomain,
            session=session,
            endpoint=endpoint.ticket_import
        )

        self.requests = RequestAPI(
            subdomain,
            session=session,
            endpoint=endpoint.requests
        )

    def get_cache_names(self):
        """
        Returns a list of current caches
        """
        return self._get_cache_mapping().keys()

    def get_cache_max(self, cache_name):
        """
        Returns the maxsize attribute of the named cache
        """
        return self._get_cache(cache_name).maxsize

    def set_cache_max(self, cache_name, maxsize, **kwargs):
        """
        Sets the maxsize attribute of the named cache
        """
        cache = self._get_cache(cache_name)
        cache.set_maxsize(maxsize, **kwargs)

    def get_cache_impl_name(self, cache_name):
        """
        Returns the name of the cache implementation for the named cache
        """
        return self._get_cache(cache_name).impl_name

    def set_cache_implementation(self, cache_name, impl_name, maxsize, **kwargs):
        """
        Changes the cache implementation for the named cache
        """
        self._get_cache(cache_name).set_cache_impl(impl_name, maxsize, **kwargs)

    def add_cache(self, object_type, cache_impl_name, maxsize, **kwargs):
        """
        Add a new cache for the named object type and cache implementation
        """
        if object_type not in self.users.object_manager.class_manager.class_mapping:
            raise ZenpyException("No such object type: %s" % object_type)
        cache_mapping = self._get_cache_mapping()
        cache_mapping[object_type] = ZenpyCache(cache_impl_name, maxsize, **kwargs)

    def delete_cache(self, cache_name):
        """
        Deletes the named cache
        """
        cache_mapping = self._get_cache_mapping()
        del cache_mapping[cache_name]

    def _get_cache(self, cache_name):
        cache_mapping = self._get_cache_mapping()
        if cache_name not in cache_mapping:
            raise ZenpyException("No such cache - %s" % cache_name)
        else:
            return cache_mapping[cache_name]

    def _get_cache_mapping(self):
        # Even though we access the users API object the cache_mapping that
        # we receive applies to all API's as it is a class attribute of ObjectManager.
        return self.users.object_manager.cache_mapping

    def _init_session(self, email, token, password, session):
        if not password and not token:
            raise ZenpyException("password or token are required!")
        elif password and token:
            raise ZenpyException("password and token are mutually exclusive!")

        session = session if session else requests.Session()
        session.auth = (email, password) if password else (email + '/token', token)
        session.headers.update(self.headers)
        return session
