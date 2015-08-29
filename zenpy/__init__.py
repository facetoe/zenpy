import logging
import sys
from zenpy.lib.api import Api

log = logging.getLogger()
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
logging.getLogger("requests").setLevel(logging.WARNING)

__author__ = 'facetoe'

class Zenpy(Api):
	def __init__(self, domain, email, token):
		Api.__init__(self, domain, email, token)
