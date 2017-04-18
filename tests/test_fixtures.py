import json

import base64
import os
import requests
from betamax import Betamax
from betamax.fixtures.unittest import BetamaxTestCase
from betamax_matchers.json_body import JSONBodyMatcher
from betamax_serializers.pretty_json import PrettyJSONSerializer
from time import sleep
from zenpy import Zenpy

from zenpy.lib.api_objects import BaseObject
from zenpy.lib.cache import should_cache, in_cache, query_cache_by_object
from zenpy.lib.generator import BaseResultGenerator

cred_path = os.path.expanduser('~/zenpy-test-credentials.json')
if os.path.exists(cred_path):
    with open(cred_path) as f:
        credentials = json.load(f)
else:
    credentials = {
        "subdomain": "facetoe1",
        "email": "example@example.com",
        "token": "not really a token"
    }


class ZenpyApiTestCase(BetamaxTestCase):
    SESSION_CLASS = requests.Session

    def setUp(self):
        config = Betamax.configure()
        config.cassette_library_dir = "tests/betamax/"
        config.default_cassette_options['record_mode'] = 'once'
        config.default_cassette_options['match_requests_on'] = ['method', 'uri']
        if credentials:
            config.define_cassette_placeholder(
                '<ZENPY-CREDENTIALS>',
                str(base64.b64encode(
                    "{}/token:{}".format(credentials['email'], credentials['token']).encode('utf-8')
                ))
            )
        super(ZenpyApiTestCase, self).setUp()

        self.recorder.register_request_matcher(JSONBodyMatcher)
        self.recorder.register_serializer(PrettyJSONSerializer)
        self.session.auth = ()
        credentials['session'] = self.session
        self.zenpy_client = Zenpy(**credentials)

    def assertInCache(self, zenpy_object):
        """ If an object should be cached, assert that it is """
        if should_cache(zenpy_object):
            return in_cache(zenpy_object)
        else:
            return True

    def assertNotInCache(self, zenpy_object):
        """ If an object should have been purged from the cache, assert that it is. """
        if should_cache(zenpy_object):
            return not in_cache(zenpy_object)
        else:
            return True

    def assertCacheUpdated(self, zenpy_object, attr, expected):
        """ If an object should be cached, assert that the specified attribute is equal to 'expected'. """
        if should_cache(zenpy_object):
            cached_object = query_cache_by_object(zenpy_object)
            # We expect it to be present
            if cached_object is None:
                return False
            return getattr(zenpy_object, attr) == expected
        else:
            return True

    def wait_for_job_status(self, job_status, request_interval=0.01, max_attempts=30):
        """ Wait until a background job has completed. """
        n = 0
        while True:
            sleep(request_interval)
            n += 1
            job_status = self.zenpy_client.job_status(id=job_status.id)
            if job_status.progress == job_status.total:
                break
            elif n > max_attempts:
                raise Exception("Too many attempts to retrieve job status!")

    def recursively_call_properties(self, zenpy_object):
        """ Recursively test that a Zenpy object's properties, and each linked property can be called without error. """
        for attr_name in dir(zenpy_object):
            if isinstance(getattr(type(zenpy_object), attr_name, None), property):
                prop_val = getattr(zenpy_object, attr_name)
                if prop_val and issubclass(prop_val.__class__, BaseObject):
                    self.recursively_call_properties(prop_val)
                elif issubclass(prop_val, BaseResultGenerator):
                    for obj in prop_val:
                        self.recursively_call_properties(obj)
