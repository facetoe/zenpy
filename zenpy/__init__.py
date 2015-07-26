import logging
import sys
from zenpy.lib.api import BaseApi

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

	def __init__(self, domain, email, token):
		self.api = BaseApi(domain, email, token)

	def search(self, **kwargs):
		return self.api.search(**kwargs)

	def users(self, **kwargs):
		return self.api.users(**kwargs)

	def tickets(self, **kwargs):
		return self.api.tickets(**kwargs)

	def groups(self, **kwargs):
		return self.api.groups(**kwargs)
