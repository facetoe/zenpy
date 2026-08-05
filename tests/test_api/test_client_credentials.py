"""
Tests for ClientCredentialsSession and Zenpy Client Credentials Grant integration.
"""

import json
from unittest import TestCase
from unittest.mock import patch

import requests
from requests_oauth2client.exceptions import InvalidClient

from zenpy import Zenpy
from zenpy.oauth import ClientCredentialsSession

TOKEN_URL = "https://testdomain.zendesk.com/oauth/tokens"
API_URL = "https://testdomain.zendesk.com/api/v2/tickets.json"
API_URL_2 = "https://testdomain.zendesk.com/api/v2/users.json"


def make_json_response(status_code, body):
    """Build a real requests.Response with a JSON body."""
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps(body).encode()
    response.headers["content-type"] = "application/json"
    return response


def make_token_response(access_token="test-access-token"):
    return make_json_response(200, {"access_token": access_token, "token_type": "bearer"})


def make_api_response(status_code=200):
    return make_json_response(status_code, {})


def make_send_side_effect(token_responses, api_responses):
    """
    side_effect for requests.Session.send, dispatching on the prepared request URL.
    Mocking at this layer (rather than Session.request) preserves the auth hook
    that requests runs during PreparedRequest construction, since that is where
    ClientCredentialsSession's OAuth2ClientCredentialsAuth attaches the token.
    """
    token_iter = iter(token_responses)
    api_iter = iter(api_responses)

    def side_effect(prepared_request, **kwargs):
        if "/oauth/tokens" in prepared_request.url:
            response = next(token_iter)
        else:
            response = next(api_iter)
        response.url = prepared_request.url
        response.request = prepared_request
        return response

    return side_effect


def new_session():
    return ClientCredentialsSession(
        subdomain="testdomain",
        client_id="client_id",
        client_secret="client_secret",
        scope="read",
    )


class TestClientCredentialsSessionInit(TestCase):
    """ClientCredentialsSession.__init__ makes no network calls."""

    @patch.object(requests.Session, "send")
    def test_no_network_on_init(self, mock_send):
        ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        mock_send.assert_not_called()

    def test_token_is_none_before_first_request(self):
        self.assertIsNone(new_session().auth.token)


class TestClientCredentialsSessionTokenFetch(TestCase):
    """Token is fetched lazily on first request."""

    @patch.object(requests.Session, "send")
    def test_token_fetched_on_first_request(self, mock_send):
        mock_send.side_effect = make_send_side_effect(
            token_responses=[make_token_response("first-token")],
            api_responses=[make_api_response(200)],
        )

        session = new_session()
        session.request("GET", API_URL)

        self.assertEqual(session.auth.token.access_token, "first-token")
        api_call = next(c for c in mock_send.call_args_list if "/oauth/tokens" not in c.args[0].url)
        self.assertEqual(api_call.args[0].headers.get("Authorization"), "Bearer first-token")

    @patch.object(requests.Session, "send")
    def test_token_reused_on_subsequent_requests(self, mock_send):
        mock_send.side_effect = make_send_side_effect(
            token_responses=[make_token_response("reused-token")],
            api_responses=[make_api_response(200), make_api_response(200)],
        )

        session = new_session()
        session.request("GET", API_URL)
        session.request("GET", API_URL_2)

        token_calls = [c for c in mock_send.call_args_list if "/oauth/tokens" in c.args[0].url]
        self.assertEqual(len(token_calls), 1)

    @patch.object(requests.Session, "send")
    def test_expires_in_passed_to_token_request(self, mock_send):
        mock_send.side_effect = make_send_side_effect(
            token_responses=[make_token_response()],
            api_responses=[make_api_response(200)],
        )

        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
            expires_in=3600,
        )
        session.request("GET", API_URL)

        token_call = next(c for c in mock_send.call_args_list if "/oauth/tokens" in c.args[0].url)
        self.assertIn("expires_in=3600", token_call.args[0].body)

    @patch.object(requests.Session, "send")
    def test_expires_in_omitted_when_not_specified(self, mock_send):
        mock_send.side_effect = make_send_side_effect(
            token_responses=[make_token_response()],
            api_responses=[make_api_response(200)],
        )

        session = new_session()
        session.request("GET", API_URL)

        token_call = next(c for c in mock_send.call_args_list if "/oauth/tokens" in c.args[0].url)
        self.assertNotIn("expires_in", token_call.args[0].body)


class TestClientCredentialsSessionTokenFetchErrors(TestCase):
    """Errors from the token endpoint propagate to the caller without retry."""

    @patch.object(requests.Session, "send")
    def test_token_fetch_error_propagates(self, mock_send):
        """An error from the token endpoint propagates to the caller."""
        mock_send.side_effect = make_send_side_effect(
            token_responses=[make_json_response(
                400, {"error": "invalid_client", "error_description": "Client not found."}
            )],
            api_responses=[],
        )

        session = new_session()
        with self.assertRaises(InvalidClient) as ctx:
            session.request("GET", API_URL)

        self.assertIn("Client not found.", str(ctx.exception))
        api_calls = [c for c in mock_send.call_args_list if "/oauth/tokens" not in c.args[0].url]
        self.assertEqual(len(api_calls), 0)

    @patch.object(requests.Session, "send")
    def test_token_endpoint_401_not_retried(self, mock_send):
        """
        A 401 from the token endpoint itself (e.g. invalid_client) is raised
        as-is, with a single POST /oauth/tokens. There is no session-level
        401 retry to accidentally double this failed token request.
        """
        mock_send.side_effect = make_send_side_effect(
            token_responses=[make_json_response(
                401, {"error": "invalid_client", "error_description": "Client authentication failed."}
            )],
            api_responses=[],
        )

        session = new_session()
        with self.assertRaises(InvalidClient):
            session.request("GET", API_URL)

        token_calls = [c for c in mock_send.call_args_list if "/oauth/tokens" in c.args[0].url]
        self.assertEqual(len(token_calls), 1)


class TestZenpyClientCredentialsInit(TestCase):
    """Zenpy uses a ClientCredentialsSession passed in via the session param as-is."""

    def test_accepts_client_credentials_session_via_session_param(self):
        session = new_session()
        client = Zenpy(subdomain="testdomain", session=session)
        self.assertIs(client.users.session, session)

    def test_creates_regular_session_for_token_auth(self):
        client = Zenpy(
            subdomain="testdomain",
            email="user@example.com",
            token="api_token",
        )
        self.assertNotIsInstance(client.users.session, ClientCredentialsSession)
        self.assertIsInstance(client.users.session, requests.Session)
