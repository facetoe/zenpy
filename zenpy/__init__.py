import logging
import sys
from zenpy.api import Api
from zenpy.exception import NoResult

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
        try:
            return self.api.query(self.api.endpoint.tickets(**kwargs))
        except NoResult:
            pass

    def comments(self, **kwargs):
        try:
            return self.api.query(self.api.endpoint.comments(**kwargs))
        except NoResult:
            pass

    def users(self, **kwargs):
        try:
            return self.api.query(self.api.endpoint.users(**kwargs))
        except NoResult:
            pass

    def search(self, **kwargs):
        try:
            return self.api.query(self.api.endpoint.search(**kwargs))
        except NoResult:
            pass