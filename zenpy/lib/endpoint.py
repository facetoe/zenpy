from datetime import datetime
import dateutil.parser
from zenpy.lib.exception import ZenpyException

__author__ = 'facetoe'


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
		for key, value in kwargs.iteritems():
			if key == 'id':
				query += self._single(self.endpoint, value)
			elif key == 'ids':
				query += self._many(self.endpoint, value)
			elif key == 'destroy_ids':
				query += self._many(self.endpoint, value, action='destroy_many.json?ids=')
			elif key == 'create_many':
				query = "".join([self.endpoint, '/create_many.json'])
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
		if 'id' not in kwargs:
			raise ZenpyException("This endpoint requires an id!")
		return self.endpoint % kwargs


class IncrementalEndpoint(BaseEndpoint):
	"""
	An IncrementalEndpoint takes a start_time parameter
	for querying the incremental api endpoint
	"""

	UNIX_TIME = "%s"

	def __call__(self, start_time=None):
		query = "start_time="
		if isinstance(start_time, datetime):
			query += start_time.strftime(self.UNIX_TIME)
		else:
			query += str(start_time)

		return self.endpoint + query + self._format_sideload(self.sideload, seperator='&')


class SearchEndpoint(BaseEndpoint):
	"""
	The SearchEndpoint is special as it takes a great variety of parameters.
	The various comparisons map to the Zendesk Search documentation as follows:

		keyword			= : (equality)
		*_greater_than 	= >
		*_less_than 	= <
		*_after 		= >
		*_before 		= <
		minus			= - (negation)
		*_between		= > < (only works with dates)
		query			= literal string, eg "product"
	"""

	ZENDESK_DATE_FORMAT = "%Y-%m-%d"

	def __call__(self, **kwargs):

		renamed_kwargs = dict()
		args = list()
		for key, value in kwargs.iteritems():
			if key.endswith('_between'):
				args.append(self.format_between(key, value))
				continue
			elif key == 'query':
				continue
			elif key == 'minus':
				if isinstance(value, list):
					[args.append("-%s" % v) for v in value]
				else:
					args.append("-%s" % value)
				continue
			elif isinstance(value, list):
				args.append(self.format_or(key, value))
				continue

			if isinstance(value, datetime):
				kwargs[key] = value.strftime(self.ZENDESK_DATE_FORMAT)
			elif isinstance(value, list) and key == 'ids':
				value = self._format_many(value)

			if key.endswith('_after'):
				renamed_kwargs[key.replace('_after', '>')] = kwargs[key]
			elif key.endswith('_before'):
				renamed_kwargs[key.replace('_before', '<')] = kwargs[key]
			elif key.endswith('_greater_than'):
				renamed_kwargs[key.replace('_greater_than', '>')] = kwargs[key]
			elif key.endswith('_less_than'):
				renamed_kwargs[key.replace('_less_than', '<')] = kwargs[key]
			else:
				renamed_kwargs.update({key + ':': '"%s"' % value})

		if 'query' in kwargs:
			endpoint = self.endpoint + 'query=' + kwargs['query'] + '+'
		else:
			endpoint = self.endpoint + 'query='

		return endpoint + self._format(*args, **renamed_kwargs)

	def format_between(self, key, values):
		if not isinstance(values, list):
			raise ZenpyException("*_between requires a list!")
		elif not len(values) == 2:
			raise ZenpyException("*_between requires exactly 2 items!")
		elif not all([isinstance(d, datetime) for d in values]):
			raise ZenpyException("*_between only works with dates!")
		key = key.replace('_between', '')
		dates = [v.strftime(self.ZENDESK_DATE_FORMAT) for v in values]
		return "%s>%s %s<%s" % (key, dates[0], key, dates[1])

	def format_or(self, key, values):
		return " ".join(['%s:"%s"' % (key, v) for v in values])


class Endpoint(object):
	"""
	The Endpoint object ties it all together.
	"""

	def __init__(self):
		self.users = PrimaryEndpoint('users', ['organizations', 'abilities', 'roles', 'identities', 'groups'])
		self.users.groups = SecondaryEndpoint('users/%(id)s/groups.json')
		self.users.organizations = SecondaryEndpoint('users/%(id)s/organizations.json')
		self.users.requested = SecondaryEndpoint('users/%(id)s/tickets/requested.json')
		self.users.cced = SecondaryEndpoint('users/%(id)s/tickets/ccd.json')
		self.users.assigned = SecondaryEndpoint('users/%(id)s/tickets/assigned.json')
		self.users.incremental = IncrementalEndpoint('incremental/users.json?')
		self.users.tags = SecondaryEndpoint('users/%(id)s/tags.json')
		self.users.group_memberships = SecondaryEndpoint('users/%(id)s/group_memberships.json')
		self.groups = PrimaryEndpoint('groups', ['users'])
		self.brands = PrimaryEndpoint('brands')
		self.topics = PrimaryEndpoint('topics')
		self.topics.tags = SecondaryEndpoint('topics/%(id)s/tags.json')
		self.tickets = PrimaryEndpoint('tickets', ['users', 'groups', 'organizations'])
		self.tickets.organizations = SecondaryEndpoint('organizations/%(id)s/tickets.json')
		self.tickets.comments = SecondaryEndpoint('tickets/%(id)s/comments.json')
		self.tickets.recent = SecondaryEndpoint('tickets/recent.json')
		self.tickets.incremental = IncrementalEndpoint('incremental/tickets.json?',
													   sideload=['users', 'groups', 'organizations'])
		self.tickets.satisfaction_ratings = SecondaryEndpoint('tickets/%(id)s/satisfaction_rating.json')
		self.tickets.events = IncrementalEndpoint('incremental/ticket_events.json?')
		self.tickets.audits = SecondaryEndpoint('tickets/%(id)s/audits.json')
		self.tickets.tags = SecondaryEndpoint('tickets/%(id)s/tags.json')
		self.tickets.metrics = SecondaryEndpoint('tickets/%(id)s/metrics.json')
		self.ticket_metrics = PrimaryEndpoint('ticket_metrics')
		self.ticket_import = PrimaryEndpoint('imports/tickets')
		self.suspended_tickets = PrimaryEndpoint('suspended_tickets')
		self.suspended_tickets.recover = SecondaryEndpoint('suspended_tickets/%(id)s/recover.json')
		self.attachments = PrimaryEndpoint('attachments')
		self.organizations = PrimaryEndpoint('organizations')
		self.organizations.incremental = IncrementalEndpoint('incremental/organizations.json?')
		self.organizations.tags = SecondaryEndpoint('organizations/%(id)s/tags.json')
		self.search = SearchEndpoint('search.json?')
		self.job_statuses = PrimaryEndpoint('job_statuses')
		self.tags = PrimaryEndpoint('tags')
		self.satisfaction_ratings = PrimaryEndpoint('satisfaction_ratings')
		self.activities = PrimaryEndpoint('activities')
		self.group_memberships = PrimaryEndpoint('group_memberships')
		self.end_user = SecondaryEndpoint('end_users/%(id)s.json')
