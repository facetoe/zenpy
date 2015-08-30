import logging
import sys
from zenpy.lib.api import UserApi, SimpleApi, TicketApi
from zenpy.lib.endpoint import Endpoint

log = logging.getLogger()
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
logging.getLogger("requests").setLevel(logging.WARNING)

__author__ = 'facetoe'


class Zenpy(object):
	def __init__(self, subdomain, email, token):
		endpoint = Endpoint()
		self.users = UserApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.users)

		self.groups = SimpleApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.groups,
			object_type='group')

		self.organizations = SimpleApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.organizations,
			object_type='organization')

		self.tickets = TicketApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.tickets)

		self.search = SimpleApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.search,
			object_type='results')

		self.topics = SimpleApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.topics,
			object_type='topic')

		self.attachments = SimpleApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.attachments,
			object_type='attachment')

		self.brands = SimpleApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.brands,
			object_type='brand')

		self.job_status = SimpleApi(
			subdomain,
			email,
			token,
			endpoint=endpoint.job_statuses,
			object_type='job_status')
