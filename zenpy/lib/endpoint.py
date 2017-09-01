import logging
import time
from datetime import datetime

from dateutil.tz import tzutc

from zenpy.lib.exception import ZenpyException
from zenpy.lib.util import is_timezone_aware, is_iterable_but_not_string

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

log = logging.getLogger(__name__)


class BaseEndpoint(object):
    """
    BaseEndpoint supplies common formatting operations.
    """

    def __init__(self, endpoint, sideload=None):
        self.endpoint = endpoint
        self.sideload = sideload or []

    @staticmethod
    def _single(endpoint, user_id):
        return "%s/%s%s" % (endpoint, user_id, '.json')

    def _many(self, endpoint, user_ids, action='show_many.json?ids='):
        return "%s/%s%s" % (endpoint, action, self._format_many(user_ids))

    @staticmethod
    def _format(*args, **kwargs):
        return '+'.join(['%s%s' % (key, value) for (key, value) in kwargs.items()] + [a for a in args])

    @staticmethod
    def _format_many(items):
        return ",".join([str(i) for i in items])

    def _format_sideload(self, items, seperator='&'):
        if isinstance(items, basestring):
            items = [items]
        return '%sinclude=%s' % (seperator, self._format_many(items))


class PrimaryEndpoint(BaseEndpoint):
    """
    A PrimaryEndpoint takes an id or list of ids and either returns the objects
    associated with them or performs actions on them (eg, update/delete).
    """

    ISO_8601_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def __call__(self, **kwargs):
        query = ""
        modifiers = []
        for key, value in kwargs.items():
            if key == 'id':
                query += self._single(self.endpoint, value)
            elif key == 'ids':
                query += self._many(self.endpoint, value)
            elif key == 'destroy_ids':
                query += self._many(self.endpoint, value, action='destroy_many.json?ids=')
            elif key == 'create_many':
                query = "".join([self.endpoint, '/create_many.json'])
            elif key == 'create_or_update_many':
                query = self.endpoint
            elif key == 'recover_ids':
                query = self._many(self.endpoint, value, action='recover_many.json?ids=')
            elif key == 'update_many':
                query = "".join([self.endpoint, '/update_many.json'])
            elif key == 'count_many':
                query = self._many(self.endpoint, value, action='count_many.json?ids=')
            elif key in ('external_id', 'external_ids'):
                external_ids = [value] if not is_iterable_but_not_string(value) else value
                query += self._many(self.endpoint, external_ids, action='show_many.json?external_ids=')
            elif key == 'update_many_external':
                query += self._many(self.endpoint, value, action='update_many.json?external_ids=')
            elif key == 'destroy_many_external':
                query += self._many(self.endpoint, value, action='destroy_many.json?external_ids=')
            elif key in ('sort_by', 'sort_order'):
                modifiers.append((key, value))
            elif key == 'permission_set':
                modifiers.append(('permission_set', value))
            elif key == 'role':
                if isinstance(value, basestring):
                    value = [value]
                for role in value:
                    modifiers.append(('role[]', role))
            elif key == 'since':
                modifiers.append((key, value.strftime(self.ISO_8601_FORMAT)))
            elif key == 'async':
                modifiers.append(('async', str(value).lower()))

        if modifiers:
            query += '&' + "&".join(["%s=%s" % (k, v) for k, v in modifiers])

        if self.endpoint not in query:
            query = self.endpoint + '.json?' + query

        if 'sideload' in kwargs and not kwargs['sideload']:
            return query
        else:
            return query + self._format_sideload(self.sideload)


class SecondaryEndpoint(BaseEndpoint):
    """
    A SecondaryEndpoint takes a single ID and returns the
    object associated with it.
    """

    def __call__(self, **kwargs):
        if not kwargs:
            raise ZenpyException("This endpoint requires arguments!")
        return self.endpoint % kwargs


class MultipleIDEndpoint(BaseEndpoint):
    def __call__(self, *args):
        if not args or len(args) < 2:
            raise ZenpyException("This endpoint requires at least two arguments!")
        return self.endpoint.format(*args)


class IncrementalEndpoint(BaseEndpoint):
    """
    An IncrementalEndpoint takes a start_time parameter
    for querying the incremental api endpoint.

    Note: The Zendesk API expects UTC time. If a timezone aware datetime object is passed
    Zenpy will convert it to UTC, however if a naive object or unix timestamp is passed there is nothing
    Zenpy can do. It is recommended to always pass timezone aware objects to this endpoint.

    :param start_time: Unix timestamp or datetime object
    """

    def __call__(self, start_time=None):
        if start_time is None:
            raise ZenpyException("Incremental Endoint requires a start_time parameter!")

        if isinstance(start_time, datetime):
            if is_timezone_aware(start_time):
                start_time = start_time.astimezone(tzutc())
            else:
                log.warning(
                    "Non timezone-aware datetime object passed to IncrementalEndpoint. "
                    "The Zendesk API expects UTC time, if this is not the case results will be incorrect!"
                )
            unix_time = time.mktime(start_time.timetuple())
        else:
            unix_time = start_time
        query = "start_time=%s" % str(unix_time)
        return self.endpoint + query + self._format_sideload(self.sideload, seperator='&')


class AttachmentEndpoint(BaseEndpoint):
    def __call__(self, **kwargs):
        query = self.endpoint
        for key, value in kwargs.items():
            if value:
                if '&' not in query:
                    query += '&'
                query += '{}={}'.format(key, value)
        return query


class SearchEndpoint(BaseEndpoint):
    """
    The search endpoint accepts all the parameters defined in the Zendesk `Search Documentation <https://developer.zendesk.com/rest_api/docs/core/search>`_.
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

    ZENDESK_DATE_FORMAT = "%Y-%m-%d"

    def __call__(self, *args, **kwargs):

        renamed_kwargs = dict()
        modifiers = list()
        sort_order = list()
        for key, value in kwargs.items():
            if isinstance(value, datetime):
                kwargs[key] = value.strftime(self.ZENDESK_DATE_FORMAT)
            elif is_iterable_but_not_string(value) and key == 'ids':
                kwargs[key] = self._format_many(value)

            if key.endswith('_between'):
                modifiers.append(self.format_between(key, value))
            elif key in ('sort_by', 'sort_order'):
                sort_order.append("%s=%s" % (key, value))
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
                renamed_kwargs.update({key + ':': '"%s"' % value})

        query = self.endpoint + 'query='
        if args:
            query += ' '.join(args) + '+'

        sort_section = ""
        if sort_order:
            sort_section += '&' + "&".join(sort_order)

        search_parameters = self._format(*modifiers, **renamed_kwargs)

        return "%(query)s%(search_parameters)s%(sort_section)s" % locals()

    def format_between(self, key, values):
        if not is_iterable_but_not_string(values):
            raise ZenpyException("*_between requires an iterable (list, set, tuple etc)")
        elif not len(values) == 2:
            raise ZenpyException("*_between requires exactly 2 items!")
        elif not all([isinstance(d, datetime) for d in values]):
            raise ZenpyException("*_between only works with dates!")
        key = key.replace('_between', '')
        dates = [v.strftime(self.ZENDESK_DATE_FORMAT) for v in values]
        return "%s>%s %s<%s" % (key, dates[0], key, dates[1])

    def format_or(self, key, values):
        return " ".join(['%s:"%s"' % (key, v) for v in values])


class RequestSearchEndpoint(BaseEndpoint):
    def __call__(self, *args, **kwargs):
        if not args:
            raise ZenpyException("You need to pass the query string as the first parameter")

        query = "query=%s" % args[0]
        result = []
        for key, value in kwargs.items():
            result.append("%s=%s" % (key, value))
        query += '&' + "&".join(result)
        return self.endpoint + query


class SatisfactionRatingEndpoint(BaseEndpoint):
    def __call__(self, score=None, sort_order=None):
        if sort_order not in ('asc', 'desc'):
            raise ZenpyException("sort_order must be one of (asc, desc)")

        base_url = self.endpoint + '?'
        if score:
            result = base_url + "score={}".format(score)
        else:
            result = base_url

        if sort_order:
            result += '&sort_order={}'.format(sort_order)
        return result


class MacroEndpoint(BaseEndpoint):
    def __call__(self, sort_order=None, sort_by=None, **kwargs):
        kwargs.pop('sideload', None)
        if sort_order and sort_order not in ('asc', 'desc'):
            raise ZenpyException("sort_order must be one of (asc, desc)")
        if sort_by and sort_by not in ('alphabetical', 'created_at', 'updated_at', 'usage_1h', 'usage_24h', 'usage_7d'):
            raise ZenpyException(
                "sort_by is invalid - https://developer.zendesk.com/rest_api/docs/core/macros#available-parameters")

        if 'id' in kwargs:
            if len(kwargs) > 1:
                raise ZenpyException("When specifying an id it must be the only parameter")
            url_out = ''
        else:
            url_out = self.endpoint + '?'

        for key, value in kwargs.items():
            if isinstance(value, bool):
                value = str(value).lower()
            if key == 'id':
                url_out += self._single(self.endpoint, value)
            else:
                url_out += '&{}={}'.format(key, value)

        if sort_order:
            url_out += '&sort_order={}'.format(sort_order)
        if sort_by:
            url_out += '&sort_by={}'.format(sort_by)
        return url_out


class ChatEndpoint(BaseEndpoint):
    def __call__(self, **kwargs):
        if len(kwargs) > 1:
            raise ZenpyException("Only expect a single keyword to the ChatEndpoint")
        endpoint_path = self.endpoint
        if 'ids' in kwargs:
            endpoint_path = "{}?ids={}".format(self.endpoint, ','.join(kwargs['ids']))
        else:
            for key, value in kwargs.items():
                if key == 'email':
                    endpoint_path = '{}/email/{}'.format(self.endpoint, value)
                elif self.endpoint == 'departments' and key == 'name':
                    endpoint_path = '{}/name/{}'.format(self.endpoint, value)
                else:
                    endpoint_path = "{}/{}".format(self.endpoint, value)
                break
        return endpoint_path


class ChatSearchEndpoint(BaseEndpoint):
    def __call__(self, *args, **kwargs):
        conditions = list()
        if args:
            conditions.append(' '.join(args))

        conditions.extend(["{}:{}".format(k, v) for k, v in kwargs.items()])
        return self.endpoint + " AND ".join(conditions)


class ViewSearchEndpoint(BaseEndpoint):
    def __call__(self, *args, **kwargs):
        params = list()
        if len(args) > 1:
            raise ZenpyException("Only query can be passed as an arg!")
        elif len(args) == 1:
            params.append("query={}".format(args[0]))
        params.extend(["{}={}".format(k, v) for k, v in kwargs.items()])
        return self.endpoint + "&".join(params).lower()


class EndpointFactory(object):
    """
    Provide access to the various endpoints.
    """

    activities = PrimaryEndpoint('activities')
    attachments = PrimaryEndpoint('attachments')
    attachments.upload = AttachmentEndpoint('uploads.json?')
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
    chats.search = ChatSearchEndpoint('chats/search?q=')
    chats.stream = ChatSearchEndpoint('stream/chats')
    end_user = SecondaryEndpoint('end_users/%(id)s.json')
    group_memberships = PrimaryEndpoint('group_memberships', sideload=['users', ' groups'])
    group_memberships.assignable = PrimaryEndpoint('group_memberships/assignable')
    group_memberships.make_default = MultipleIDEndpoint('users/{}/group_memberships/{}/make_default.json')
    groups = PrimaryEndpoint('groups', ['users'])
    groups.memberships = SecondaryEndpoint('groups/%(id)s/memberships.json')
    groups.memberships_assignable = SecondaryEndpoint('groups/%(id)s/memberships/assignable.json')
    job_statuses = PrimaryEndpoint('job_statuses')
    macros = MacroEndpoint('macros', sideload=['app_installation', 'categories', 'permissions', 'usage_1h', 'usage_24h',
                                               'usage_7d', 'usage_30d'])
    macros.apply = SecondaryEndpoint('macros/%(id)s/apply.json')
    organization_memberships = PrimaryEndpoint('organization_memberships')
    organizations = PrimaryEndpoint('organizations', ['abilities'])
    organizations.external = SecondaryEndpoint('organizations/search.json?external_id=%(id)s')
    organizations.incremental = IncrementalEndpoint('incremental/organizations.json?')
    organizations.organization_fields = PrimaryEndpoint('organization_fields')
    organizations.organization_memberships = SecondaryEndpoint('organizations/%(id)s/organization_memberships.json')
    organizations.requests = SecondaryEndpoint('organizations/%(id)s/requests.json')
    organizations.tags = SecondaryEndpoint('organizations/%(id)s/tags.json')
    organizations.create_or_update = PrimaryEndpoint('organizations/create_or_update')
    requests = PrimaryEndpoint('requests')
    requests.ccd = PrimaryEndpoint("requests/ccd")
    requests.comments = SecondaryEndpoint('requests/%(id)s/comments.json')
    requests.open = PrimaryEndpoint("requests/open")
    requests.search = RequestSearchEndpoint('requests/search.json?')
    requests.solved = PrimaryEndpoint("requests/solved")
    satisfaction_ratings = SatisfactionRatingEndpoint('satisfaction_ratings')
    satisfaction_ratings.create = SecondaryEndpoint('tickets/%(id)s/satisfaction_rating.json')
    search = SearchEndpoint('search.json?')
    sharing_agreements = PrimaryEndpoint('sharing_agreements')
    sla_policies = PrimaryEndpoint('slas/policies')
    sla_policies.definitions = PrimaryEndpoint('slas/policies/definitions')
    suspended_tickets = PrimaryEndpoint('suspended_tickets')
    suspended_tickets.recover = SecondaryEndpoint('suspended_tickets/%(id)s/recover.json')
    tags = PrimaryEndpoint('tags')
    ticket_fields = PrimaryEndpoint('ticket_fields')
    ticket_import = PrimaryEndpoint('imports/tickets')
    ticket_metrics = PrimaryEndpoint('ticket_metrics')
    tickets = PrimaryEndpoint('tickets',
                              ['users', 'groups', 'organizations', 'last_audits', 'metric_sets', 'dates',
                               'sharing_agreements', 'comment_count', 'incident_counts', 'ticket_forms',
                               'metric_events', 'slas'])
    tickets.audits = SecondaryEndpoint('tickets/%(id)s/audits.json',
                                       sideload=['users', 'organizations', 'groups', 'tickets'])
    tickets.comments = SecondaryEndpoint('tickets/%(id)s/comments.json')
    tickets.events = IncrementalEndpoint('incremental/ticket_events.json?', sideload=['comment_events'])
    tickets.incremental = IncrementalEndpoint('incremental/tickets.json?',
                                              sideload=['users', 'groups', 'organizations', 'last_audits',
                                                        'metric_sets', 'dates',
                                                        'sharing_agreements', 'comment_count', 'incident_counts',
                                                        'ticket_forms',
                                                        'metric_events', 'slas'])
    tickets.metrics = SecondaryEndpoint('tickets/%(id)s/metrics.json')
    tickets.metrics.incremental = IncrementalEndpoint('incremental/ticket_metric_events.json?')
    tickets.organizations = SecondaryEndpoint('organizations/%(id)s/tickets.json')
    tickets.recent = SecondaryEndpoint('tickets/recent.json')
    tickets.tags = SecondaryEndpoint('tickets/%(id)s/tags.json')
    tickets.macro = MultipleIDEndpoint('tickets/{0}/macros/{1}/apply.json')
    tickets.merge = SecondaryEndpoint('tickets/%(id)s/merge.json')
    topics = PrimaryEndpoint('topics')
    topics.tags = SecondaryEndpoint('topics/%(id)s/tags.json')
    user_fields = PrimaryEndpoint('user_fields')
    users = PrimaryEndpoint('users',
                            ['organizations', 'abilities', 'roles', 'identities', 'groups', 'open_ticket_count'])
    users.assigned = SecondaryEndpoint('users/%(id)s/tickets/assigned.json')
    users.cced = SecondaryEndpoint('users/%(id)s/tickets/ccd.json')
    users.create_or_update = PrimaryEndpoint('users/create_or_update')
    users.create_or_update_many = PrimaryEndpoint('users/create_or_update_many.json')
    users.group_memberships = SecondaryEndpoint('users/%(id)s/group_memberships.json')
    users.groups = SecondaryEndpoint('users/%(id)s/groups.json')
    users.incremental = IncrementalEndpoint('incremental/users.json?')
    users.me = SecondaryEndpoint('users/me.json')
    users.merge = SecondaryEndpoint('users/%(id)s/merge.json')
    users.organization_memberships = SecondaryEndpoint('users/%(id)s/organization_memberships.json')
    users.organizations = SecondaryEndpoint('users/%(id)s/organizations.json')
    users.related = SecondaryEndpoint('users/%(id)s/related.json')
    users.requested = SecondaryEndpoint('users/%(id)s/tickets/requested.json')
    users.requests = SecondaryEndpoint('users/%(id)s/requests.json', sideload=['users', 'organizations'])
    users.tags = SecondaryEndpoint('users/%(id)s/tags.json')
    users.identities = SecondaryEndpoint('users/%(id)s/identities.json')
    users.identities.show = MultipleIDEndpoint('users/{0}/identities/{1}.json')
    users.identities.update = MultipleIDEndpoint('users/{0}/identities/{1}.json')
    users.identities.make_primary = MultipleIDEndpoint('users/{0}/identities/{1}/make_primary')
    users.identities.verify = MultipleIDEndpoint('users/{0}/identities/{1}/verify')
    users.identities.request_verification = MultipleIDEndpoint('users/{0}/identities/{1}/request_verification.json')
    users.identities.delete = MultipleIDEndpoint('users/{0}/identities/{1}.json')
    views = PrimaryEndpoint('views', sideload=['app_installation', 'permissions'])
    views.active = PrimaryEndpoint('views/active')
    views.compact = PrimaryEndpoint('views/compact')
    views.count = SecondaryEndpoint('views/%(id)s/count.json')
    views.tickets = SecondaryEndpoint('views/%(id)s/tickets')
    views.execute = SecondaryEndpoint('views/%(id)s/execute.json')
    views.export = SecondaryEndpoint('views/%(id)s/export.json')
    views.search = ViewSearchEndpoint('views/search.json?')

    def __new__(cls, endpoint_name):
        return getattr(cls, endpoint_name)
