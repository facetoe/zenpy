import logging
import sys

from zenpy.lib.api import UserApi, Api, TicketApi, OranizationApi, SuspendedTicketApi
from zenpy.lib.endpoint import Endpoint

log = logging.getLogger()
log.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
logging.getLogger("requests").setLevel(logging.WARNING)

__author__ = 'facetoe'


class Zenpy(object):
	def __init__(self, subdomain, email, token, debug=False):
		if debug:
			log.setLevel(logging.DEBUG)

		endpoint = Endpoint()

		self.users = UserApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.users)

		self.groups = Api(
			subdomain,
			email,
			token,
			endpoint=endpoint.groups,
			object_type='group')

		self.organizations = OranizationApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.organizations)

		self.tickets = TicketApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.tickets)

		self.suspended_tickets = SuspendedTicketApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.suspended_tickets)

		self.search = Api(
			subdomain,
			email,
			token,
			endpoint=endpoint.search,
			object_type='results')

		self.topics = Api(
			subdomain,
			email,
			token,
			endpoint=endpoint.topics,
			object_type='topic')

		self.attachments = Api(
			subdomain,
			email,
			token,
			endpoint=endpoint.attachments,
			object_type='attachment')

		self.brands = Api(
			subdomain,
			email,
			token,
			endpoint=endpoint.brands,
			object_type='brand')

		self.job_status = Api(
			subdomain,
			email,
			token,
			endpoint=endpoint.job_statuses,
			object_type='job_status')

		self.tags = Api(
			subdomain,
			email,
			token,
			endpoint=endpoint.tags,
			object_type='tag')
