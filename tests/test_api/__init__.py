import json

import base64
import os
import requests
from betamax import Betamax
from betamax_matchers.json_body import JSONBodyMatcher
from betamax_serializers.pretty_json import PrettyJSONSerializer
from zenpy import Zenpy

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
    zenpy_client, recorder = configure()
    with recorder.use_cassette(cassette_name="setup_package-create-tickets", serialize_with='prettyjson'):
        err_template = "{} found in test environment, bailing out!"
        assert_empty(zenpy_client.tickets(), err_template.format("Tickets"))
        assert_empty(zenpy_client.users(), err_template.format("Users"),
                     ignore_func=lambda x: x.role != "admin" or x.name != "Mailer-daemon")


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
    config.default_cassette_options['match_requests_on'] = ['method', 'uri']
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
    recorder.register_request_matcher(JSONBodyMatcher)
    recorder.register_serializer(PrettyJSONSerializer)
    return zenpy_client, recorder
