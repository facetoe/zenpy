import logging
import sys
from zenpy.api import Api

__author__ = 'facetoe'
log = logging.getLogger()
log.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
logging.getLogger("requests").setLevel(logging.WARNING)


class Zenpy(object):
    api = None

    def __init__(self, subdomain, email, token):
        self.api = Api(subdomain, email, token)

    def tickets(self, **kwargs):
        return self.api.query(self.api.endpoint.tickets(**kwargs))

    def comments(self, **kwargs):
        return self.api.query(self.api.endpoint.comments(**kwargs))

    def users(self, **kwargs):
        return self.api.query(self.api.endpoint.users(**kwargs))

    def search(self, **kwargs):
        return self.api.query(self.api.endpoint.search(**kwargs))
