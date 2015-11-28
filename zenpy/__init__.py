import logging
import sys

from zenpy.lib.api import UserApi, Api, TicketApi, OranizationApi, SuspendedTicketApi, EndUserApi, TicketImportAPI, \
    RequestAPI
from zenpy.lib.endpoint import Endpoint
from zenpy.lib.exception import ZenpyException
from zenpy.lib.zenpy_cache import ZenpyCache

log = logging.getLogger()
log.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
logging.getLogger("requests").setLevel(logging.WARNING)

__author__ = 'facetoe'


class Zenpy(object):
    def __init__(self, subdomain, email, token=None, password=None, debug=False):
        if not password and not token:
            raise ZenpyException("password or token are required!")
        elif password and token:
            raise ZenpyException("password and token are mutually exclusive!")

        if debug:
            log.setLevel(logging.DEBUG)

        self.endpoint = Endpoint()

        self.users = UserApi(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.users)

        self.groups = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.groups,
            object_type='group')

        self.organizations = OranizationApi(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.organizations)

        self.tickets = TicketApi(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.tickets)

        self.suspended_tickets = SuspendedTicketApi(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.suspended_tickets)

        self.search = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.search,
            object_type='results')

        self.topics = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.topics,
            object_type='topic')

        self.attachments = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.attachments,
            object_type='attachment')

        self.brands = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.brands,
            object_type='brand')

        self.job_status = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.job_statuses,
            object_type='job_status')

        self.tags = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.tags,
            object_type='tag')

        self.satisfaction_ratings = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.satisfaction_ratings,
            object_type='satisfaction_rating'
        )

        self.activities = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.activities,
            object_type='activity'
        )

        self.group_memberships = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.group_memberships,
            object_type='group_membership'
        )

        self.end_user = EndUserApi(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.end_user
        )

        self.ticket_metrics = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.ticket_metrics,
            object_type='ticket_metric'
        )

        self.ticket_fields = Api(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.ticket_fields,
            object_type='ticket_field'
        )

        self.ticket_import = TicketImportAPI(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.ticket_import
        )

        self.requests = RequestAPI(
            subdomain,
            email,
            token=token,
            password=password,
            endpoint=self.endpoint.requests
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
