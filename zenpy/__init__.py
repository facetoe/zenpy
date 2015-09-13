import logging
import sys

from zenpy.lib.api import UserApi, Api, TicketApi, OranizationApi, SuspendedTicketApi
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
	def __init__(self, subdomain, email, token=None, password=None, debug=False):
		if not password and not token:
			raise ZenpyException("password or token are required!")
		elif password and token:
			raise ZenpyException("password and token are mutually exclusive!")

		if debug:
			log.setLevel(logging.DEBUG)

		endpoint = Endpoint()

		self.users = UserApi(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.users)

		self.groups = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.groups,
			object_type='group')

		self.organizations = OranizationApi(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.organizations)

		self.tickets = TicketApi(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.tickets)

		self.suspended_tickets = SuspendedTicketApi(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.suspended_tickets)

		self.search = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.search,
			object_type='results')

		self.topics = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.topics,
			object_type='topic')

		self.attachments = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.attachments,
			object_type='attachment')

		self.brands = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.brands,
			object_type='brand')

		self.job_status = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.job_statuses,
			object_type='job_status')

		self.tags = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.tags,
			object_type='tag')

		self.satisfaction_ratings = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.satisfaction_ratings,
			object_type='satisfaction_rating'
		)

		self.activities = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.activities,
			object_type='activity'
		)

		self.group_memberships = Api(
			subdomain,
			email,
			token=token,
			password=password,
			endpoint=endpoint.group_memberships,
			object_type='group_membership'
		)
