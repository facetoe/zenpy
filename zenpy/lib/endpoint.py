import logging
from datetime import date
from datetime import datetime

from requests.utils import quote

from zenpy.lib.exception import ZenpyException
from zenpy.lib.util import is_iterable_but_not_string, to_unix_ts

__author__ = 'facetoe'

try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str, bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring

try:
    from urllib import urlencode
    from urlparse import urlunsplit, SplitResult
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import urlunsplit, SplitResult

log = logging.getLogger(__name__)


class Url(object):
    def __init__(self, path, params=None, netloc=None):
        self.scheme = 'https'
        self.path = path
        self.params = params or {}
        self.netloc = netloc

    def build(self):
        query = "&".join({"{}={}".format(k, v) for k, v in self.params.items()})
        return urlunsplit(SplitResult(
            scheme=self.scheme,
            netloc=self.netloc,
            path=self.path,
            query=query,
            fragment=None))

    def prefix_path(self, prefix):
        self.path = "{}/{}".format(prefix, self.path)

    def __str__(self):
        return "{}({})".format(type(self).__name__, ", ".join({"{}={}".format(k, v) for k, v in vars(self).items()}))


class BaseEndpoint(object):
    ISO_8601_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
    ZENDESK_DATE_FORMAT = "%Y-%m-%d"

    def __init__(self, endpoint):
        self.endpoint = endpoint


class PrimaryEndpoint(BaseEndpoint):
    """
    The PrimaryEndpoint handles the most common endpoint operations.
    """

    def __call__(self, **kwargs):
        parameters = {}
        path = self.endpoint
        for key, value in kwargs.items():
            if key == 'id':
                path += "/{}.json".format(value)
            elif key == 'ids':
                path += '/show_many.json'
                parameters[key] = ",".join(map(str, value))
            elif key == 'destroy_ids':
                path += '/destroy_many.json'
                parameters['ids'] = ",".join(map(str, value))
            elif key == 'create_many':
                path += '/create_many.json'
            elif key == '/create_or_update_many':
                path = self.endpoint
            elif key == 'recover_ids':
                path += '/recover_many.json'
                parameters[key] = ",".join(map(str, value))
            elif key == 'update_many':
                path += '/update_many.json'
            elif key == 'count_many':
                path += '/count_many.json'
                parameters[key] = ",".join(map(str, value))
            elif key == 'external_id' and path == 'tickets':
                parameters[key] = value
            elif key in ('external_id', 'external_ids'):
                external_ids = [value] if not is_iterable_but_not_string(value) else value
                path += '/show_many.json'
                parameters['external_ids'] = ",".join(external_ids)
            elif key == 'update_many_external':
                path += '/update_many.json'
                parameters['external_ids'] = ",".join(map(str, value))
            elif key == 'destroy_many_external':
                path += '/destroy_many.json'
                parameters['external_ids'] = ",".join(map(str, value))
            elif key == 'label_names':
                parameters[key] = ",".join(value)
            elif key in ('sort_by', 'sort_order', 'permission_set', 'page', 'limit', 'cursor', 'filter_by',):
                parameters[key] = value
            elif key == 'since':
                parameters[key] = value.strftime(self.ISO_8601_FORMAT)
            elif key == 'async':
                parameters[key] = str(value).lower()
            elif key == 'include':
                if is_iterable_but_not_string(value):
                    parameters[key] = ",".join(value)
                elif value:
                    parameters[key] = value
            elif key in ('since_id', 'ticket_id', 'issue_id'):  # Jira integration
                parameters[key] = value

            # this is a bit of a hack
            elif key == 'role':
                if isinstance(value, basestring) or len(value) == 1:
                    parameters['role[]'] = value
                else:
                    parameters['role[]'] = value[0] + '&' + "&".join(('role[]={}'.format(role) for role in value[1:]))
            elif key.endswith('ids'):
                # if it looks like a type of unknown id, send it through as such
                parameters[key] = ",".join(map(str, value))

        if path == self.endpoint and not path.endswith('.json'):
            path += '.json'
        return Url(path=path, params=parameters)


class SecondaryEndpoint(BaseEndpoint):
    def __call__(self, id, **kwargs):
        return Url(self.endpoint % dict(id=id), params=kwargs)


class MultipleIDEndpoint(BaseEndpoint):
    def __call__(self, *args):
        if not args or len(args) < 2:
            raise ZenpyException("This endpoint requires at least two arguments!")
        return Url(self.endpoint.format(*args))


class IncrementalEndpoint(BaseEndpoint):
    """
    An IncrementalEndpoint takes a start_time parameter
    for querying the incremental api endpoint.

    Note: The Zendesk API expects UTC time. If a timezone aware datetime object is passed
    Zenpy will convert it to UTC, however if a naive object or unix timestamp is passed there is nothing
    Zenpy can do. It is recommended to always pass timezone aware objects to this endpoint.

    :param start_time: unix timestamp or datetime object
    :param include: list of items to sideload
    """

    def __call__(self, start_time=None, include=None):
        if start_time is None:
            raise ZenpyException("Incremental Endpoint requires a start_time parameter!")

        elif isinstance(start_time, datetime):
            unix_time = to_unix_ts(start_time)
        else:
            unix_time = start_time

        params = dict(start_time=str(unix_time))
        if include is not None:
            if is_iterable_but_not_string(include):
                params.update(dict(include=",".join(include)))
            else:
                params.update(dict(include=include))
        return Url(self.endpoint, params=params)

class ChatIncrementalEndpoint(BaseEndpoint):
    """
    An ChatsIncrementalEndpoint takes parameters
    for querying the chats incremental api endpoint.

    Note: The Zendesk API expects UTC time. If a timezone aware datetime object is passed
    Zenpy will convert it to UTC, however if a naive object or unix timestamp is passed there is nothing
    Zenpy can do. It is recommended to always pass timezone aware objects to this endpoint.

    :param start_time: unix timestamp or datetime object
    :param fields: list of chat fields to load without "chats(xxx)". Defaults to "*"
    """

    def __call__(self, start_time=None, **kwargs):
        if start_time is None:
            raise ZenpyException("Incremental Endpoint requires a start_time parameter!")

        elif isinstance(start_time, datetime):
            unix_time = to_unix_ts(start_time)
        else:
            unix_time = start_time

        params = kwargs
        params.update(dict(start_time=str(unix_time)))

        if 'fields' in kwargs:
            if is_iterable_but_not_string(kwargs['fields']):
                f =  ",".join(kwargs['fields'])
            else:
                f = kwargs['fields']
        else:
            f = "*"
        params.update(dict(fields="chats(" + f + ")"))

        return Url(self.endpoint, params=params)


class AttachmentEndpoint(BaseEndpoint):
    def __call__(self, **kwargs):
        return Url(self.endpoint, params={k: v for k, v in kwargs.items() if v is not None})


class SearchEndpoint(BaseEndpoint):
    """
    The search endpoint accepts all the parameters defined in the Zendesk
    `Search Documentation <https://developer.zendesk.com/rest_api/docs/core/search>`_.
    Zenpy defines several keywords that are mapped to the Zendesk comparison operators:

    +-----------------+------------------+
    | **Keyword**     | **Operator**     |
    +-----------------+------------------+
    | keyword         | : (equality)     |
    +-----------------+------------------+
    | \*_greater_than | > (numeric|type) |
    +-----------------+------------------+
    | \*_less_than    | < (numeric|type) |
    +-----------------+------------------+
    | \*_after        | > (time|date)    |
    +-----------------+------------------+
    | \*_before       | < (time|date)    |
    +-----------------+------------------+
    | minus           | \- (negation)    |
    +-----------------+------------------+
    | \*_between      | > < (dates only) |
    +-----------------+------------------+

    For example the call:

    .. code:: python

      zenpy.search("zenpy", created_between=[yesterday, today], type='ticket', minus='negated')

    Would generate the following API call:
    ::
        /api/v2/search.json?query=zenpy+created>2015-08-29 created<2015-08-30+type:ticket+-negated


    """

    def __call__(self, query=None, **kwargs):

        renamed_kwargs = dict()
        modifiers = list()
        params = dict()
        for key, value in kwargs.items():
            if isinstance(value, date):
                kwargs[key] = value.strftime(self.ZENDESK_DATE_FORMAT)
            elif isinstance(key, datetime):
                kwargs[key] = value.strftime(self.ISO_8601_FORMAT)
            elif is_iterable_but_not_string(value) and key == 'ids':
                kwargs[key] = ", ".join(map(str, value))
            if key.endswith('_between'):
                modifiers.append(self.format_between(key, value))
            elif key in ('sort_by', 'sort_order'):
                params[key] = value
            elif key.endswith('_after'):
                renamed_kwargs[key.replace('_after', '>')] = kwargs[key]
            elif key.endswith('_before'):
                renamed_kwargs[key.replace('_before', '<')] = kwargs[key]
            elif key.endswith('_greater_than'):
                renamed_kwargs[key.replace('_greater_than', '>')] = kwargs[key]
            elif key.endswith('_less_than'):
                renamed_kwargs[key.replace('_less_than', '<')] = kwargs[key]
            elif key == 'minus':
                if is_iterable_but_not_string(value):
                    [modifiers.append("-%s" % v) for v in value]
                else:
                    modifiers.append("-%s" % value)
            elif is_iterable_but_not_string(value):
                modifiers.append(self.format_or(key, value))
            else:
                if isinstance(value, str) and value.count(' ') > 0:
                    value = '"{}"'.format(value)
                renamed_kwargs.update({key + ':': '%s' % value})

        search_query = ['%s%s' % (key, value) for (key, value) in renamed_kwargs.items()]
        search_query.extend(modifiers)
        if query is not None:
            search_query.insert(0, quote(query))
        params['query'] = ' '.join(search_query)

        return Url(self.endpoint, params)

    def format_between(self, key, values):
        if not is_iterable_but_not_string(values):
            raise ValueError("*_between requires an iterable (list, set, tuple etc)")
        elif not len(values) == 2:
            raise ZenpyException("*_between requires exactly 2 items!")
        for value in values:
            if not isinstance(value, datetime):
                raise ValueError("*_between only works with datetime objects!")
            elif value.tzinfo is not None and value.utcoffset().total_seconds() != 0:
                log.warning("search parameter '{}' requires UTC time, results likely incorrect.".format(key))
        key = key.replace('_between', '')
        dates = [v.strftime(self.ISO_8601_FORMAT) for v in values]
        return "%s>%s %s<%s" % (key, dates[0], key, dates[1])

    def format_or(self, key, values):
        return " ".join(['%s:"%s"' % (key, v) for v in values])


class RequestSearchEndpoint(BaseEndpoint):
    def __call__(self, query, **kwargs):
        kwargs['query'] = query
        return Url(self.endpoint, params=kwargs)


class HelpDeskSearchEndpoint(BaseEndpoint):
    def __call__(self, query='', **kwargs):
        processed_kwargs = dict()
        for key, value in kwargs.items():
            if isinstance(value, datetime):
                processed_kwargs[key] = value.strftime(self.ZENDESK_DATE_FORMAT)
            elif is_iterable_but_not_string(value):
                processed_kwargs[key] = ",".join(value)
            else:
                processed_kwargs[key] = value
        processed_kwargs['query'] = query
        return Url(self.endpoint, params=processed_kwargs)


class SatisfactionRatingEndpoint(BaseEndpoint):
    def __call__(self, score=None, sort_order=None, start_time=None, end_time=None):
        if sort_order and sort_order not in ('asc', 'desc'):
            raise ZenpyException("sort_order must be one of (asc, desc)")
        params = dict()
        if score:
            params['score'] = score
        if sort_order:
            params['sort_order'] = sort_order
        if start_time:
            params['start_time'] = to_unix_ts(start_time)
        if end_time:
            params['end_time'] = to_unix_ts(end_time)
        return Url(self.endpoint, params=params)


class MacroEndpoint(BaseEndpoint):
    def __call__(self, sort_order=None, sort_by=None, **kwargs):
        if sort_order and sort_order not in ('asc', 'desc'):
            raise ZenpyException("sort_order must be one of (asc, desc)")
        if sort_by and sort_by not in ('alphabetical', 'created_at', 'updated_at', 'usage_1h', 'usage_24h', 'usage_7d'):
            raise ZenpyException(
                "sort_by is invalid - https://developer.zendesk.com/rest_api/docs/core/macros#available-parameters")

        if 'id' in kwargs:
            if len(kwargs) > 1:
                raise ZenpyException("When specifying an id it must be the only parameter")

        params = dict()
        path = self.endpoint
        for key, value in kwargs.items():
            if isinstance(value, bool):
                value = str(value).lower()
            if key == 'id':
                path += "/{}.json".format(value)
            else:
                params[key] = value

        if sort_order:
            params['sort_order'] = sort_order
        if sort_by:
            params['sort_by'] = sort_by

        if path == self.endpoint:
            path += '.json'

        return Url(path, params=params)


class ChatEndpoint(BaseEndpoint):
    def __call__(self, **kwargs):
        if len(kwargs) > 1:
            raise ZenpyException("Only expect a single keyword to the ChatEndpoint")
        endpoint_path = self.endpoint
        params = dict()
        if 'ids' in kwargs:
            endpoint_path = self.endpoint
            params['ids'] = ','.join(kwargs['ids'])
        else:
            for key, value in kwargs.items():
                if key == 'email':
                    endpoint_path = '{}/email/{}'.format(self.endpoint, value)
                elif self.endpoint == 'departments' and key == 'name':
                    endpoint_path = '{}/name/{}'.format(self.endpoint, value)
                else:
                    endpoint_path = "{}/{}".format(self.endpoint, value)
                break
        return Url(endpoint_path, params=params)

class ChatSearchEndpoint(BaseEndpoint):
    def __call__(self, *args, **kwargs):
        conditions = list()
        if args:
            conditions.append(' '.join(args))
        conditions.extend(["{}:{}".format(k, v) for k, v in kwargs.items()])
        query = " AND ".join(conditions)
        return Url(self.endpoint, params=dict(q=query))


class ViewSearchEndpoint(BaseEndpoint):
    def __call__(self, query, **kwargs):
        kwargs['query'] = query
        return Url(self.endpoint, params=kwargs)


class EndpointFactory(object):
    """
    Provide access to the various endpoints.
    """

    activities = PrimaryEndpoint('activities')
    attachments = PrimaryEndpoint('attachments')
    attachments.upload = AttachmentEndpoint('uploads.json')
    automations = PrimaryEndpoint('automations')
    brands = PrimaryEndpoint('brands')
    chats = ChatEndpoint('chats')
    chats.account = ChatEndpoint('account')
    chats.agents = ChatEndpoint('agents')
    chats.agents.me = ChatEndpoint("agents/me")
    chats.bans = ChatEndpoint('bans')
    chats.departments = ChatEndpoint('departments')
    chats.goals = ChatEndpoint('goals')
    chats.triggers = ChatEndpoint('triggers')
    chats.shortcuts = ChatEndpoint('shortcuts')
    chats.visitors = ChatEndpoint('visitors')
    chats.search = ChatSearchEndpoint('chats/search')
    chats.stream = ChatSearchEndpoint('stream/chats')
    chats.incremental = ChatIncrementalEndpoint('incremental/chats')
    custom_agent_roles = PrimaryEndpoint('custom_roles')
    dynamic_contents = PrimaryEndpoint('dynamic_content/items')
    dynamic_contents.variants = SecondaryEndpoint('dynamic_content/items/%(id)s/variants.json')
    dynamic_contents.variants.show = MultipleIDEndpoint('dynamic_content/items/{}/variants/{}.json')
    dynamic_contents.variants.create = SecondaryEndpoint('dynamic_content/items/%(id)s/variants.json')
    dynamic_contents.variants.create_many = SecondaryEndpoint('dynamic_content/items/%(id)s/variants/create_many.json')
    dynamic_contents.variants.update = MultipleIDEndpoint('dynamic_content/items/{}/variants/{}.json')
    dynamic_contents.variants.update_many = SecondaryEndpoint('dynamic_content/items/%(id)s/variants/update_many.json')
    dynamic_contents.variants.delete = MultipleIDEndpoint('dynamic_content/items/{}/variants/{}.json')
    end_user = SecondaryEndpoint('end_users/%(id)s.json')
    group_memberships = PrimaryEndpoint('group_memberships')
    group_memberships.assignable = PrimaryEndpoint('group_memberships/assignable')
    group_memberships.make_default = MultipleIDEndpoint('users/{}/group_memberships/{}/make_default.json')
    groups = PrimaryEndpoint('groups')
    groups.memberships = SecondaryEndpoint('groups/%(id)s/memberships.json')
    groups.memberships_assignable = SecondaryEndpoint('groups/%(id)s/memberships/assignable.json')
    groups.users = SecondaryEndpoint('groups/%(id)s/users.json')
    job_statuses = PrimaryEndpoint('job_statuses')
    locales = PrimaryEndpoint('locales')
    links = PrimaryEndpoint('services/jira/links')
    macros = MacroEndpoint('macros')
    macros.apply = SecondaryEndpoint('macros/%(id)s/apply.json')
    macros.attachments = SecondaryEndpoint('macros/%(id)s/attachments.json')
    macros.attachments_upload = SecondaryEndpoint('macros/%(id)s/attachments.json')
    macros.attachments_upload_unassociated = SecondaryEndpoint('macros/attachments.json')

    nps = PrimaryEndpoint('nps')
    nps.recipients_incremental = IncrementalEndpoint('nps/incremental/recipients.json')
    nps.responses_incremental = IncrementalEndpoint('nps/incremental/responses.json')
    organization_memberships = PrimaryEndpoint('organization_memberships')
    organization_fields = PrimaryEndpoint('organization_fields')
    organization_fields.reorder = PrimaryEndpoint('organization_fields/reorder.json')
    organizations = PrimaryEndpoint('organizations')
    organizations.external = SecondaryEndpoint('organizations/search.json?external_id=%(id)s')
    organizations.incremental = IncrementalEndpoint('incremental/organizations.json')
    organizations.organization_fields = PrimaryEndpoint('organization_fields')
    organizations.organization_memberships = SecondaryEndpoint('organizations/%(id)s/organization_memberships.json')
    organizations.requests = SecondaryEndpoint('organizations/%(id)s/requests.json')
    organizations.tags = SecondaryEndpoint('organizations/%(id)s/tags.json')
    organizations.create_or_update = PrimaryEndpoint('organizations/create_or_update')
    organizations.users = SecondaryEndpoint('organizations/%(id)s/users.json')
    requests = PrimaryEndpoint('requests')
    requests.ccd = PrimaryEndpoint("requests/ccd")
    requests.comments = SecondaryEndpoint('requests/%(id)s/comments.json')
    requests.open = PrimaryEndpoint("requests/open")
    requests.search = RequestSearchEndpoint('requests/search.json')
    requests.solved = PrimaryEndpoint("requests/solved")
    satisfaction_ratings = SatisfactionRatingEndpoint('satisfaction_ratings')
    satisfaction_ratings.create = SecondaryEndpoint('tickets/%(id)s/satisfaction_rating.json')
    schedules = PrimaryEndpoint('business_hours/schedules')
    search = SearchEndpoint('search.json')
    search.count = SearchEndpoint('search/count.json')
    sharing_agreements = PrimaryEndpoint('sharing_agreements')
    sla_policies = PrimaryEndpoint('slas/policies')
    sla_policies.definitions = PrimaryEndpoint('slas/policies/definitions')
    skips = PrimaryEndpoint('skips')
    suspended_tickets = PrimaryEndpoint('suspended_tickets')
    suspended_tickets.recover = SecondaryEndpoint('suspended_tickets/%(id)s/recover.json')
    tags = PrimaryEndpoint('tags')
    targets = PrimaryEndpoint('targets')
    ticket_fields = PrimaryEndpoint('ticket_fields')
    ticket_field_options = SecondaryEndpoint('ticket_fields/%(id)s/options.json')
    ticket_field_options.show = MultipleIDEndpoint('ticket_fields/{}/options/{}.json')
    ticket_field_options.update = SecondaryEndpoint('ticket_fields/%(id)s/options.json')
    ticket_field_options.delete = MultipleIDEndpoint('ticket_fields/{}/options/{}.json')
    ticket_forms = PrimaryEndpoint('ticket_forms')
    ticket_import = PrimaryEndpoint('imports/tickets')
    ticket_metrics = PrimaryEndpoint('ticket_metrics')
    ticket_metric_events = IncrementalEndpoint('incremental/ticket_metric_events.json')
    tickets = PrimaryEndpoint('tickets')
    tickets.audits = SecondaryEndpoint('tickets/%(id)s/audits.json')
    tickets.audits.cursor = PrimaryEndpoint('ticket_audits')
    tickets.comments = SecondaryEndpoint('tickets/%(id)s/comments.json')
    tickets.comments.redact = MultipleIDEndpoint('tickets/{0}/comments/{1}/redact.json')
    tickets.deleted = PrimaryEndpoint('deleted_tickets')
    tickets.events = IncrementalEndpoint('incremental/ticket_events.json')
    tickets.incremental = IncrementalEndpoint('incremental/tickets.json')
    tickets.metrics = SecondaryEndpoint('tickets/%(id)s/metrics.json')
    tickets.metrics.incremental = IncrementalEndpoint('incremental/ticket_metric_events.json')
    tickets.organizations = SecondaryEndpoint('organizations/%(id)s/tickets.json')
    tickets.recent = SecondaryEndpoint('tickets/recent.json')
    tickets.tags = SecondaryEndpoint('tickets/%(id)s/tags.json')
    tickets.macro = MultipleIDEndpoint('tickets/{0}/macros/{1}/apply.json')
    tickets.merge = SecondaryEndpoint('tickets/%(id)s/merge.json')
    tickets.skips = SecondaryEndpoint('tickets/%(id)s/skips.json')
    topics = PrimaryEndpoint('topics')
    topics.tags = SecondaryEndpoint('topics/%(id)s/tags.json')
    triggers = PrimaryEndpoint('triggers')
    user_fields = PrimaryEndpoint('user_fields')
    users = PrimaryEndpoint('users')
    users.assigned = SecondaryEndpoint('users/%(id)s/tickets/assigned.json')
    users.cced = SecondaryEndpoint('users/%(id)s/tickets/ccd.json')
    users.create_or_update = PrimaryEndpoint('users/create_or_update')
    users.create_or_update_many = PrimaryEndpoint('users/create_or_update_many.json')
    users.group_memberships = SecondaryEndpoint('users/%(id)s/group_memberships.json')
    users.deleted = PrimaryEndpoint("deleted_users")
    users.groups = SecondaryEndpoint('users/%(id)s/groups.json')
    users.incremental = IncrementalEndpoint('incremental/users.json')
    users.me = PrimaryEndpoint('users/me')
    users.merge = SecondaryEndpoint('users/%(id)s/merge.json')
    users.organization_memberships = SecondaryEndpoint('users/%(id)s/organization_memberships.json')
    users.organizations = SecondaryEndpoint('users/%(id)s/organizations.json')
    users.related = SecondaryEndpoint('users/%(id)s/related.json')
    users.requested = SecondaryEndpoint('users/%(id)s/tickets/requested.json')
    users.requests = SecondaryEndpoint('users/%(id)s/requests.json')
    users.tags = SecondaryEndpoint('users/%(id)s/tags.json')
    users.set_password = SecondaryEndpoint('users/%(id)s/password.json')
    users.identities = SecondaryEndpoint('users/%(id)s/identities.json')
    users.identities.show = MultipleIDEndpoint('users/{0}/identities/{1}.json')
    users.identities.update = MultipleIDEndpoint('users/{0}/identities/{1}.json')
    users.identities.make_primary = MultipleIDEndpoint('users/{0}/identities/{1}/make_primary')
    users.identities.verify = MultipleIDEndpoint('users/{0}/identities/{1}/verify')
    users.identities.request_verification = MultipleIDEndpoint('users/{0}/identities/{1}/request_verification.json')
    users.identities.delete = MultipleIDEndpoint('users/{0}/identities/{1}.json')
    users.skips = SecondaryEndpoint('users/%(id)s/skips.json')
    views = PrimaryEndpoint('views')
    views.active = PrimaryEndpoint('views/active')
    views.compact = PrimaryEndpoint('views/compact')
    views.count = SecondaryEndpoint('views/%(id)s/count.json')
    views.tickets = SecondaryEndpoint('views/%(id)s/tickets')
    views.execute = SecondaryEndpoint('views/%(id)s/execute.json')
    views.export = SecondaryEndpoint('views/%(id)s/export.json')
    views.search = ViewSearchEndpoint('views/search.json')
    recipient_addresses = PrimaryEndpoint('recipient_addresses')

    class Dummy(object): pass

    talk = Dummy()
    talk.current_queue_activity = PrimaryEndpoint('channels/voice/stats/current_queue_activity')
    talk.agents_activity = PrimaryEndpoint('channels/voice/stats/agents_activity')
    talk.availability = SecondaryEndpoint('channels/voice/availabilities/%(id)s.json')
    talk.account_overview = PrimaryEndpoint('channels/voice/stats/account_overview')
    talk.agents_overview = PrimaryEndpoint('channels/voice/stats/agents_overview')
    talk.phone_numbers = PrimaryEndpoint('channels/voice/phone_numbers.json')

    help_centre = Dummy()
    help_centre.articles = PrimaryEndpoint('help_center/articles')
    help_centre.articles.create = SecondaryEndpoint('help_center/sections/%(id)s/articles.json')
    help_centre.articles.comments = SecondaryEndpoint('help_center/articles/%(id)s/comments.json')
    help_centre.articles.comments_update = MultipleIDEndpoint('help_center/articles/{}/comments/{}.json')
    help_centre.articles.comments_delete = MultipleIDEndpoint('help_center/articles/{}/comments/{}.json')
    help_centre.articles.comment_show = MultipleIDEndpoint('help_center/articles/{}/comments/{}.json')
    help_centre.articles.user_comments = SecondaryEndpoint('help_center/users/%(id)s/comments.json')
    help_centre.articles.labels = SecondaryEndpoint('help_center/articles/%(id)s/labels.json')
    help_centre.articles.translations = SecondaryEndpoint('help_center/articles/%(id)s/translations.json')
    help_centre.articles.create_translation = SecondaryEndpoint('help_center/articles/%(id)s/translations.json')
    help_centre.articles.missing_translations = SecondaryEndpoint(
        'help_center/articles/%(id)s/translations/missing.json')
    help_centre.articles.update_translation = MultipleIDEndpoint('help_center/articles/{}/translations/{}.json')
    help_centre.articles.show_translation = MultipleIDEndpoint('help_center/articles/{}/translations/{}.json')
    help_centre.articles.delete_translation = SecondaryEndpoint('help_center/translations/%(id)s.json')
    help_centre.articles.search = HelpDeskSearchEndpoint('help_center/articles/search.json')
    help_centre.articles.subscriptions = SecondaryEndpoint('help_center/articles/%(id)s/subscriptions.json')
    help_centre.articles.subscriptions_delete = MultipleIDEndpoint('help_center/articles/{}/subscriptions/{}.json')
    help_centre.articles.votes = SecondaryEndpoint('help_center/articles/%(id)s/votes.json')
    help_centre.articles.votes.up = SecondaryEndpoint('help_center/articles/%(id)s/up.json')
    help_centre.articles.votes.down = SecondaryEndpoint('help_center/articles/%(id)s/down.json')
    help_centre.articles.comment_votes = MultipleIDEndpoint('help_center/articles/{}/comments/{}/votes.json')
    help_centre.articles.comment_votes.up = MultipleIDEndpoint('help_center/articles/{}/comments/{}/up.json')
    help_centre.articles.comment_votes.down = MultipleIDEndpoint('help_center/articles/{}/comments/{}/down.json')
    help_centre.articles.incremental = IncrementalEndpoint('help_center/incremental/articles.json')

    help_centre.labels = PrimaryEndpoint('help_center/articles/labels')
    help_centre.labels.create = SecondaryEndpoint('help_center/articles/%(id)s/labels.json')
    help_centre.labels.delete = MultipleIDEndpoint('help_center/articles/{}/labels/{}.json')

    help_centre.attachments = SecondaryEndpoint('help_center/articles/%(id)s/attachments.json')
    help_centre.attachments.inline = SecondaryEndpoint('help_center/articles/%(id)s/attachments/inline.json')
    help_centre.attachments.block = SecondaryEndpoint('help_center/articles/%(id)s/attachments/block.json')
    help_centre.attachments.create = SecondaryEndpoint('help_center/articles/%(id)s/attachments.json')
    help_centre.attachments.create_unassociated = PrimaryEndpoint('help_center/articles/attachments')
    help_centre.attachments.delete = SecondaryEndpoint('help_center/articles/attachments/%(id)s.json')
    help_centre.attachments.bulk_attachments = SecondaryEndpoint('help_center/articles/%(id)s/bulk_attachments.json')

    help_centre.categories = PrimaryEndpoint('help_center/categories')
    help_centre.categories.articles = SecondaryEndpoint('help_center/categories/%(id)s/articles.json')
    help_centre.categories.sections = SecondaryEndpoint('help_center/categories/%(id)s/sections.json')
    help_centre.categories.translations = SecondaryEndpoint('help_center/categories/%(id)s/translations.json')
    help_centre.categories.create_translation = SecondaryEndpoint('help_center/categories/%(id)s/translations.json')
    help_centre.categories.missing_translations = SecondaryEndpoint(
        'help_center/categories/%(id)s/translations/missing.json')
    help_centre.categories.update_translation = MultipleIDEndpoint('help_center/categories/{}/translations/{}.json')
    help_centre.categories.delete_translation = SecondaryEndpoint('help_center/translations/%(id)s.json')

    help_centre.sections = PrimaryEndpoint('help_center/sections')
    help_centre.sections.create = SecondaryEndpoint('help_center/categories/%(id)s/sections.json')
    help_centre.sections.articles = SecondaryEndpoint('help_center/sections/%(id)s/articles.json')
    help_centre.sections.translations = SecondaryEndpoint('help_center/sections/%(id)s/translations.json')
    help_centre.sections.create_translation = SecondaryEndpoint('help_center/sections/%(id)s/translations.json')
    help_centre.sections.missing_translations = SecondaryEndpoint(
        'help_center/sections/%(id)s/translations/missing.json')
    help_centre.sections.update_translation = MultipleIDEndpoint('help_center/sections/{}/translations/{}.json')
    help_centre.sections.delete_translation = SecondaryEndpoint('help_center/translations/%(id)s.json')
    help_centre.sections.subscriptions = SecondaryEndpoint('help_center/sections/%(id)s/subscriptions.json')
    help_centre.sections.subscriptions_delete = MultipleIDEndpoint('help_center/sections/{}/subscriptions/{}.json')
    help_centre.sections.access_policies = SecondaryEndpoint('help_center/sections/%(id)s/access_policy.json')

    help_centre.topics = PrimaryEndpoint("community/topics")
    help_centre.topics.posts = SecondaryEndpoint('community/topics/%(id)s/posts.json')
    help_centre.topics.subscriptions = SecondaryEndpoint('community/topics/%(id)s/subscriptions.json')
    help_centre.topics.subscriptions_delete = MultipleIDEndpoint('community/topics/{}/subscriptions/{}.json')
    help_centre.topics.access_policies = SecondaryEndpoint('community/topics/%(id)s/access_policy.json')

    help_centre.posts = PrimaryEndpoint('community/posts')
    help_centre.posts.subscriptions = SecondaryEndpoint('community/posts/%(id)s/subscriptions.json')
    help_centre.posts.subscriptions_delete = MultipleIDEndpoint('community/posts/{}/subscriptions/{}.json')

    help_centre.posts.comments = SecondaryEndpoint('community/posts/%(id)s/comments.json')
    help_centre.posts.comments.delete = MultipleIDEndpoint('community/posts/{}/comments/{}.json')
    help_centre.posts.comments.update = MultipleIDEndpoint('community/posts/{}/comments/{}.json')

    help_centre.posts.votes = SecondaryEndpoint('community/posts/%(id)s/votes.json')
    help_centre.posts.votes.up = SecondaryEndpoint('community/posts/%(id)s/up.json')
    help_centre.posts.votes.down = SecondaryEndpoint('community/posts/%(id)s/down.json')
    help_centre.posts.comments.comment_votes = MultipleIDEndpoint('community/posts/{}/comments/{}/votes.json')
    help_centre.posts.comments.comment_votes.up = MultipleIDEndpoint('community/posts/{}/comments/{}/up.json')
    help_centre.posts.comments.comment_votes.down = MultipleIDEndpoint('community/posts/{}/comments/{}/down.json')

    help_centre.user_segments = PrimaryEndpoint('help_center/user_segments')
    help_centre.user_segments.applicable = PrimaryEndpoint('help_center/user_segments/applicable')
    help_centre.user_segments.sections = SecondaryEndpoint('help_center/user_segments/%(id)s/sections.json')
    help_centre.user_segments.topics = SecondaryEndpoint('help_center/user_segments/%(id)s/topics.json')

    def __new__(cls, endpoint_name):
        return getattr(cls, endpoint_name)
