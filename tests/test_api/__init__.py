import base64
import json

import os
import requests
from betamax import Betamax
from betamax.matchers import URIMatcher
from betamax_serializers.pretty_json import PrettyJSONSerializer

from zenpy import Zenpy

cred_path = os.path.expanduser('~/zenpy-test-credentials.json')

if os.path.exists(cred_path):
    with open(cred_path) as f:
        credentials = json.load(f)
else:
    credentials = {
        "subdomain": "d3v-zenpydev",
        "email": "example@example.com",
        "token": "not really a token"
    }


def chunk_action(iterable, action, wait_action=None, ignore_func=None, batch_size=100):
    """
    Ensure action is executed on chunks not greater than batch_size elements.
    If the callable wait_action is not None, it will be passed the results of
    executing action.
    """
    batch = list()

    def process_batch():
        batch_len = len(batch)
        result = action(batch)
        if wait_action:
            wait_action(result)
        del batch[:]
        return batch_len

    count = 0
    for n, item in enumerate(iterable, start=1):
        if n % batch_size == 0:
            if ignore_func and not ignore_func(item):
                batch.append(item)
            count += process_batch()
        else:
            batch.append(item)
    if batch:
        count += process_batch()
    return count


def setup_package():
    print("setup_package called")


def assert_empty(iterable, message, ignore_func=None):
    if not ignore_func and len(iterable) > 0:
        raise Exception(message)
    for zenpy_object in iterable:
        if not ignore_func(zenpy_object):
            raise Exception(message)


def teardown_package():
    print("teardown_package called")
    zenpy_client, recorder = configure()
    with recorder.use_cassette(cassette_name="teardown_package", serialize_with='prettyjson'):
        n = chunk_action(zenpy_client.tickets(), zenpy_client.tickets.delete)
        print("Deleted {} tickets".format(n))
        n = chunk_action(zenpy_client.users(), zenpy_client.users.delete, ignore_func=lambda x: x.role == "admin")
        print("Deleted {} users".format(n))


def configure():
    config = Betamax.configure()
    config.cassette_library_dir = "tests/test_api/betamax/"
    config.default_cassette_options['record_mode'] = 'once'
    config.default_cassette_options['match_requests_on'] = ['method', 'path_matcher']
    if credentials:
        auth_key = 'token' if 'token' in credentials else 'password'
        config.define_cassette_placeholder(
            '<ZENPY-CREDENTIALS>',
            str(base64.b64encode(
                "{}/token:{}".format(credentials['email'], credentials[auth_key]).encode('utf-8')
            ))
        )
    session = requests.Session()
    credentials['session'] = session
    zenpy_client = Zenpy(**credentials)
    recorder = Betamax(session=session)

    class PathMatcher(URIMatcher):
        """
        I use trial accounts for testing Zenpy and as such the subdomain is always changing.
        This matcher ignores the netloc section of the parsed URL which prevents the tests
        failing when the subdomain is changed.
        """
        name = 'path_matcher'

        def parse(self, uri):
            parse_result = super(PathMatcher, self).parse(uri)
            parse_result.pop('netloc')
            return parse_result

    Betamax.register_request_matcher(PathMatcher)
    recorder.register_serializer(PrettyJSONSerializer)
    return zenpy_client, recorder
