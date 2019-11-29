import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry

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
    TicketFormApi,
    OrganizationFieldsApi,
    JiraLinkApi, SkipApi, TalkApi,
    CustomAgentRolesApi,
    SearchApi)

from zenpy.lib.cache import ZenpyCache, ZenpyCacheManager
from zenpy.lib.endpoint import EndpointFactory
from zenpy.lib.exception import ZenpyException
from zenpy.lib.mapping import ZendeskObjectMapping

log = logging.getLogger()

__author__ = 'facetoe'
__version__ = '2.0.10'


class Zenpy(object):
    """"""

    DEFAULT_TIMEOUT = 60.0

    def __init__(self, subdomain=None,
                 email=None,
                 token=None,
                 oauth_token=None,
                 password=None,
                 session=None,
                 timeout=None,
                 ratelimit_budget=None,
                 proactive_ratelimit=None,
                 proactive_ratelimit_request_interval=10,
                 disable_cache=False):
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
        :param ratelimit_budget: maximum time to spend being rate limited
        :param proactive_ratelimit: user specified rate limit.
        :param proactive_ratelimit_request_interval: seconds to wait when over proactive_ratelimit.
        :param disable_cache: disable caching of objects
        """

        session = self._init_session(email, token, oauth_token, password, session)

        timeout = timeout or self.DEFAULT_TIMEOUT

        self.cache = ZenpyCacheManager(disable_cache)

        config = dict(
            subdomain=subdomain,
            session=session,
            timeout=timeout,
            ratelimit=int(proactive_ratelimit) if proactive_ratelimit is not None else None,
            ratelimit_budget=int(ratelimit_budget) if ratelimit_budget is not None else None,
            ratelimit_request_interval=int(proactive_ratelimit_request_interval),
            cache=self.cache
        )

        self.users = UserApi(config)
        self.user_fields = Api(config, object_type='user_field')
        self.groups = GroupApi(config)
        self.macros = MacroApi(config)
        self.organizations = OrganizationApi(config)
        self.organization_memberships = OrganizationMembershipApi(config)
        self.organization_fields = OrganizationFieldsApi(config)
        self.tickets = TicketApi(config)
        self.suspended_tickets = SuspendedTicketApi(config, object_type='suspended_ticket')
        self.search = SearchApi(config)
        self.topics = Api(config, object_type='topic')
        self.attachments = AttachmentApi(config)
        self.brands = BrandApi(config, object_type='brand')
        self.job_status = Api(config, object_type='job_status', endpoint=EndpointFactory('job_statuses'))
        self.jira_links = JiraLinkApi(config)
        self.tags = Api(config, object_type='tag')
        self.satisfaction_ratings = SatisfactionRatingApi(config)
        self.sharing_agreements = SharingAgreementAPI(config)
        self.skips = SkipApi(config)
        self.activities = Api(config, object_type='activity')
        self.group_memberships = GroupMembershipApi(config)
        self.end_user = EndUserApi(config)
        self.ticket_metrics = Api(config, object_type='ticket_metric')
        self.ticket_metric_events = Api(config, object_type='ticket_metric_events')
        self.ticket_fields = TicketFieldApi(config)
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
        self.dynamic_content = DynamicContentApi(config)
        self.targets = TargetApi(config, object_type='target')
        self.talk = TalkApi(config)
        self.custom_agent_roles = CustomAgentRolesApi(config, object_type='custom_agent_role')

    @staticmethod
    def http_adapter_kwargs():
        """
        Provides Zenpy's default HTTPAdapter args for those users providing their own adapter.
        """

        return dict(
            # Transparently retry requests that are safe to retry, with the exception of 429. This is handled
            # in the Api._call_api() method.
            max_retries=Retry(
                total=3,
                status_forcelist=[r for r in Retry.RETRY_AFTER_STATUS_CODES if r != 429],
                respect_retry_after_header=False
            )
        )

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

        headers = {'User-Agent': 'Zenpy/{}'.format(__version__)}
        session.headers.update(headers)
        return session

    def get_cache_names(self):
        """
        Returns a list of current caches
        """
        return self.cache.mapping.keys()

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
        self.cache.mapping[object_type] = ZenpyCache(cache_impl_name, maxsize, **kwargs)

    def delete_cache(self, cache_name):
        """
        Deletes the named cache
        """
        del self.cache.mapping[cache_name]

    def purge_cache(self, cache_name):
        """
        Purges the named cache.
        """
        self.cache.purge_cache(cache_name)

    def disable_caching(self):
        """
        Disable caching of objects.
        """
        self.cache.disable()

    def enable_caching(self):
        """
        Enable caching of objects.
        """
        self.cache.enable()

    def caching_status(self):
        """
        Returns caching status.
        """
        self.cache.status()

    def caching_engines(self):
        """
        Returns available caching engines.
        """
        self.cache.get_cache_engines()

    def _get_cache(self, cache_name):
        if cache_name not in self.cache.mapping:
            raise ZenpyException("No such cache - %s" % cache_name)
        else:
            return self.cache.mapping[cache_name]
