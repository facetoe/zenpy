import logging

import requests
from requests.adapters import HTTPAdapter

from zenpy.lib.api import (
    UserApi,
    Api,
    TicketApi,
    OrganizationApi,
    SuspendedTicketApi,
    EndUserApi,
    TicketImportAPI,
    RequestAPI,
    OrganizationMembershipApi,
    AttachmentApi,
    SharingAgreementAPI,
    SatisfactionRatingApi,
    MacroApi,
    GroupApi,
    ViewApi,
    SlaPolicyApi,
    ChatApi,
    GroupMembershipApi,
    HelpCentreApi,
    RecipientAddressApi,
    NpsApi, TicketFieldApi,
    TriggerApi,
    AutomationApi,
    DynamicContentApi,
    TargetApi,
    BrandApi,
    TicketFormApi)

from zenpy.lib.cache import ZenpyCache, cache_mapping, purge_cache
from zenpy.lib.endpoint import EndpointFactory
from zenpy.lib.exception import ZenpyException
from zenpy.lib.mapping import ZendeskObjectMapping

log = logging.getLogger()

__author__ = 'facetoe'


class Zenpy(object):
    """"""

    DEFAULT_TIMEOUT = 60.0

    @staticmethod
    def http_adapter_kwargs():
        """
        Provides Zenpy's default HTTPAdapter args for those users providing their own adapter.
        """

        return dict(
            # http://docs.python-requests.org/en/latest/api/?highlight=max_retries#requests.adapters.HTTPAdapter
            max_retries=3
        )

    def __init__(self, subdomain=None,
                 email=None,
                 token=None,
                 oauth_token=None,
                 password=None,
                 session=None,
                 timeout=None,
                 ratelimit=None,
                 ratelimit_budget=None):
        """
        Python Wrapper for the Zendesk API.

        There are several ways to authenticate with the Zendesk API:
            * Email and password
            * Email and Zendesk API token
            * Email and OAuth token
            * Existing authenticated Requests Session object.


        :param subdomain: your Zendesk subdomain
        :param email: email address
        :param token: Zendesk API token
        :param oauth_token: OAuth token
        :param password: Zendesk password
        :param session: existing Requests Session object
        :param timeout: global timeout on API requests.
        :param ratelimit: user specified rate limit
        :param ratelimit_budget: maximum time to spend being rate limited
        """

        session = self._init_session(email, token, oauth_token, password, session)

        timeout = timeout or self.DEFAULT_TIMEOUT

        config = dict(
            subdomain=subdomain,
            session=session,
            timeout=timeout,
            ratelimit=int(ratelimit) if ratelimit is not None else None,
            ratelimit_budget=int(ratelimit_budget) if ratelimit_budget is not None else None
        )

        self.users = UserApi(config)
        self.user_fields = Api(config, object_type='user_field')
        self.groups = GroupApi(config)
        self.macros = MacroApi(config)
        self.organizations = OrganizationApi(config)
        self.organization_memberships = OrganizationMembershipApi(config)
        self.tickets = TicketApi(config)
        self.suspended_tickets = SuspendedTicketApi(config, object_type='suspended_ticket')
        self.search = Api(config, object_type='results', endpoint=EndpointFactory('search'))
        self.topics = Api(config, object_type='topic')
        self.attachments = AttachmentApi(config)
        self.brands = BrandApi(config, object_type='brand')
        self.job_status = Api(config, object_type='job_status', endpoint=EndpointFactory('job_statuses'))
        self.tags = Api(config, object_type='tag')
        self.satisfaction_ratings = SatisfactionRatingApi(config)
        self.sharing_agreements = SharingAgreementAPI(config)
        self.activities = Api(config, object_type='activity')
        self.group_memberships = GroupMembershipApi(config)
        self.end_user = EndUserApi(config)
        self.ticket_metrics = Api(config, object_type='ticket_metric')
        self.ticket_fields = TicketFieldApi(config, object_type='ticket_field')
        self.ticket_forms = TicketFormApi(config, object_type='ticket_form')
        self.ticket_import = TicketImportAPI(config)
        self.requests = RequestAPI(config)
        self.chats = ChatApi(config, endpoint=EndpointFactory('chats'))
        self.views = ViewApi(config)
        self.sla_policies = SlaPolicyApi(config)
        self.help_center = HelpCentreApi(config)
        self.recipient_addresses = RecipientAddressApi(config)
        self.nps = NpsApi(config)
        self.triggers = TriggerApi(config, object_type='trigger')
        self.automations = AutomationApi(config, object_type='automation')
        self.dynamic_content = DynamicContentApi(config, object_type='dynamic_content_item')
        self.targets = TargetApi(config, object_type='target')

    def _init_session(self, email, token, oath_token, password, session):
        if not session:
            session = requests.Session()
            # Workaround for possible race condition - https://github.com/kennethreitz/requests/issues/3661
            session.mount('https://', HTTPAdapter(**self.http_adapter_kwargs()))

        if not hasattr(session, 'authorized') or not session.authorized:
            # session is not an OAuth session that has been authorized, so authorize the session.
            if not password and not token and not oath_token:
                raise ZenpyException("password, token or oauth_token are required!")
            elif password and token:
                raise ZenpyException("password and token "
                                     "are mutually exclusive!")
            if password:
                session.auth = (email, password)
            elif token:
                session.auth = ('%s/token' % email, token)
            elif oath_token:
                session.headers.update({'Authorization': 'Bearer %s' % oath_token})
            else:
                raise ZenpyException("Invalid arguments to _init_session()!")

        headers = {'User-Agent': 'Zenpy/1.2'}
        session.headers.update(headers)
        return session

    def get_cache_names(self):
        """
        Returns a list of current caches
        """
        return cache_mapping.keys()

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
        if object_type not in ZendeskObjectMapping.class_mapping:
            raise ZenpyException("No such object type: %s" % object_type)
        cache_mapping[object_type] = ZenpyCache(cache_impl_name, maxsize, **kwargs)

    def delete_cache(self, cache_name):
        """
        Deletes the named cache
        """
        del cache_mapping[cache_name]

    def purge_cache(self, cache_name):
        """
        Purges the named cache.
        """
        purge_cache(cache_name)

    def _get_cache(self, cache_name):
        if cache_name not in cache_mapping:
            raise ZenpyException("No such cache - %s" % cache_name)
        else:
            return cache_mapping[cache_name]
