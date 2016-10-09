from datetime import datetime

from zenpy.lib.exception import ZenpyException

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
            elif key in ('sort_by', 'sort_order'):
                modifiers.append((key, value))
            elif key == 'since':
                modifiers.append((key, value.strftime(self.ISO_8601_FORMAT)))

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


class IncrementalEndpoint(BaseEndpoint):
    """
    An IncrementalEndpoint takes a start_time parameter
    for querying the incremental api endpoint
    """

    UNIX_TIME = "%s"

    def __call__(self, **kwargs):
        query = "start_time="
        if 'start_time' in kwargs:
            if isinstance(kwargs['start_time'], datetime):
                query += kwargs['start_time'].strftime(self.UNIX_TIME)
            else:
                query += str(kwargs['start_time'])
            return self.endpoint + query + self._format_sideload(self.sideload, seperator='&')

        raise ZenpyException("Incremental Endoint requires a start_time parameter!")


class AttachmentEndpoint(BaseEndpoint):
    def __call__(self, **kwargs):
        query = self.endpoint
        for key, value in kwargs.items():
            if value:
                if not '&' in query:
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
            elif isinstance(value, list) and key == 'ids':
                kwargs[key] = self._format_many(value)
            elif isinstance(value, list):
                modifiers.append(self.format_or(key, value))

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
                if isinstance(value, list):
                    [modifiers.append("-%s" % v) for v in value]
                else:
                    modifiers.append("-%s" % value)
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
        if not isinstance(values, list) and not isinstance(values, tuple):
            raise ZenpyException("*_between requires a list or tuple!")
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


class Endpoint(object):
    """
    The Endpoint object ties it all together.
    """

    users = PrimaryEndpoint('users', ['organizations', 'abilities', 'roles', 'identities', 'groups'])
    users.me = SecondaryEndpoint('users/me.json')
    users.groups = SecondaryEndpoint('users/%(id)s/groups.json')
    users.organizations = SecondaryEndpoint('users/%(id)s/organizations.json')
    users.requested = SecondaryEndpoint('users/%(id)s/tickets/requested.json')
    users.cced = SecondaryEndpoint('users/%(id)s/tickets/ccd.json')
    users.assigned = SecondaryEndpoint('users/%(id)s/tickets/assigned.json')
    users.incremental = IncrementalEndpoint('incremental/users.json?')
    users.tags = SecondaryEndpoint('users/%(id)s/tags.json')
    users.group_memberships = SecondaryEndpoint('users/%(id)s/group_memberships.json')
    users.requests = SecondaryEndpoint('users/%(id)s/requests.json')
    users.related = SecondaryEndpoint('users/%(id)s/related.json')
    users.create_or_update = PrimaryEndpoint('users/create_or_update')
    users.create_or_update_many = PrimaryEndpoint('users/create_or_update_many.json')
    users.organization_memberships = SecondaryEndpoint('users/%(id)s/organization_memberships.json')
    user_fields = PrimaryEndpoint('user_fields')
    groups = PrimaryEndpoint('groups', ['users'])
    brands = PrimaryEndpoint('brands')
    topics = PrimaryEndpoint('topics')
    topics.tags = SecondaryEndpoint('topics/%(id)s/tags.json')
    tickets = PrimaryEndpoint('tickets', ['users', 'groups', 'organizations'])
    tickets.organizations = SecondaryEndpoint('organizations/%(id)s/tickets.json')
    tickets.comments = SecondaryEndpoint('tickets/%(id)s/comments.json')
    tickets.recent = SecondaryEndpoint('tickets/recent.json')
    tickets.incremental = IncrementalEndpoint('incremental/tickets.json?',
                                              sideload=['users', 'groups', 'organizations'])
    tickets.satisfaction_ratings = SecondaryEndpoint('tickets/%(id)s/satisfaction_rating.json')
    tickets.events = IncrementalEndpoint('incremental/ticket_events.json?')
    tickets.audits = SecondaryEndpoint('tickets/%(id)s/audits.json')
    tickets.tags = SecondaryEndpoint('tickets/%(id)s/tags.json')
    tickets.metrics = SecondaryEndpoint('tickets/%(id)s/metrics.json')
    tickets.metrics.incremental = IncrementalEndpoint('incremental/ticket_metric_events.json?')
    ticket_metrics = PrimaryEndpoint('ticket_metrics')
    ticket_import = PrimaryEndpoint('imports/tickets')
    ticket_fields = PrimaryEndpoint('ticket_fields')
    suspended_tickets = PrimaryEndpoint('suspended_tickets')
    suspended_tickets.recover = SecondaryEndpoint('suspended_tickets/%(id)s/recover.json')
    attachments = PrimaryEndpoint('attachments')
    attachments.upload = AttachmentEndpoint('uploads.json?')
    organization_memberships = PrimaryEndpoint('organization_memberships')
    organizations = PrimaryEndpoint('organizations')
    organizations.incremental = IncrementalEndpoint('incremental/organizations.json?')
    organizations.tags = SecondaryEndpoint('organizations/%(id)s/tags.json')
    organizations.organization_fields = PrimaryEndpoint('organization_fields')
    organizations.requests = SecondaryEndpoint('organizations/%(id)s/requests.json')
    organizations.external = SecondaryEndpoint('organizations/search.json?external_id=%(id)s')
    organizations.organization_memberships = SecondaryEndpoint('organizations/%(id)s/organization_memberships.json')
    search = SearchEndpoint('search.json?')
    job_statuses = PrimaryEndpoint('job_statuses')
    tags = PrimaryEndpoint('tags')
    satisfaction_ratings = PrimaryEndpoint('satisfaction_ratings')
    activities = PrimaryEndpoint('activities')
    group_memberships = PrimaryEndpoint('group_memberships')
    end_user = SecondaryEndpoint('end_users/%(id)s.json')
    requests = PrimaryEndpoint('requests')
    requests.open = PrimaryEndpoint("requests/open")
    requests.solved = PrimaryEndpoint("requests/solved")
    requests.ccd = PrimaryEndpoint("requests/ccd")
    requests.comments = SecondaryEndpoint('requests/%(id)s/comments.json')
    requests.search = RequestSearchEndpoint('requests/search.json?')
