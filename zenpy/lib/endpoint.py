from datetime import datetime
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

	def _many(self, endpoint, user_ids):
		return "%s/%s%s" % (endpoint, 'show_many.json?ids=', self._format_many(user_ids))

	def _destroy_many(self, endpoint, ids):
		return "%s/%s%s" % (endpoint, 'destroy_many.json?ids=', self._format_many(ids))

	@staticmethod
	def _format(*args, **kwargs):
		return '+'.join(['%s%s' % (key, value) for (key, value) in kwargs.items()] + [a for a in args])

	@staticmethod
	def _format_many(items):
		return ",".join([str(i) for i in items])

	def _format_sideload(self, items):
		if isinstance(items, basestring):
			items = [items]
		return '?include=' + self._format_many(items)


class PrimaryEndpoint(BaseEndpoint):
	"""
	A PrimaryEndpoint takes an id or list of ids and either returns the objects
	associated with them or performs actions on them (eg, update/delete).
	"""
	def __call__(self, **kwargs):
		query = ""
		modifiers = []
		for key, value in kwargs.iteritems():
			if key == 'id':
				query += self._single(self.endpoint, value)
			elif key == 'ids':
				query += self._many(self.endpoint, value)
			elif key == 'destroy_ids':
				query += self._destroy_many(self.endpoint, value)
			elif key == 'create_many':
				query = "".join([self.endpoint, '/create_many.json'])
			elif key == 'update_many':
				query = "".join([self.endpoint, '/update_many.json'])
			elif key in ('sort_by', 'sort_order'):
				modifiers.append((key, value))

		if modifiers:
			query += '&' + "&".join(["%s=%s" % (k, v) for k, v in modifiers])

		if self.endpoint not in query:
			query = self.endpoint + '.json' + query

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
		return self.endpoint % kwargs


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
				renamed_kwargs[''] = self.format_between(key, value)
				continue
			elif key == 'query':
				continue
			elif key == 'minus':
				if isinstance(value, list):
					[args.append("-%s" % v) for v in value]
				else:
					args.append("-%s" % value)
				continue

			if isinstance(value, datetime):
				kwargs[key] = value.strftime(self.ZENDESK_DATE_FORMAT)
			elif isinstance(value, list):
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
				renamed_kwargs.update({key + ':': value})

		if 'query' in kwargs:
			endpoint = self.endpoint + 'query=' + kwargs['query'] + '+'
		else:
			endpoint = self.endpoint + 'query='

		return endpoint + self._format(*args, **renamed_kwargs)

	def format_between(self, key, value):
		if not isinstance(value, list):
			raise ZenpyException("*_between requires a list!")
		elif not len(value) == 2:
			raise ZenpyException("*_between requires exactly 2 items!")
		elif not all([isinstance(d, datetime) for d in value]):
			raise ZenpyException("*_between only works with dates!")
		key = key.replace('_between', '')
		dates = [v.strftime(self.ZENDESK_DATE_FORMAT) for v in value]
		return "%s>%s %s<%s" % (key, dates[0], key, dates[1])


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
		self.groups = PrimaryEndpoint('groups', ['users'])
		self.brands = PrimaryEndpoint('brands')
		self.topics = PrimaryEndpoint('topics')
		self.tickets = PrimaryEndpoint('tickets', ['users', 'groups', 'organizations'])
		self.tickets.organizations = SecondaryEndpoint('organizations/%(id)s/tickets.json')
		self.tickets.comments = SecondaryEndpoint('tickets/%(id)s/comments.json')
		self.tickets.recent = SecondaryEndpoint('tickets/recent.json')
		self.attachments = PrimaryEndpoint('attachments')
		self.organizations = PrimaryEndpoint('organizations')
		self.search = SearchEndpoint('search.json?')
		self.job_statuses = PrimaryEndpoint('job_statuses')
