"""
Tests for ClientCredentialsSession and Zenpy Client Credentials Grant integration.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from zenpy import Zenpy, ClientCredentialsSession

TOKEN_URL = "https://testdomain.zendesk.com/oauth/tokens"
API_URL = "https://testdomain.zendesk.com/api/v2/tickets.json"
API_URL_2 = "https://testdomain.zendesk.com/api/v2/users.json"


def make_token_response(access_token="test-access-token"):
    """Create a mock response for the OAuth token endpoint."""
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"access_token": access_token, "token_type": "bearer"}
    return response


def make_api_response(status_code=200):
    """Create a mock response for a Zendesk API call."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {}
    return response


def _extract_url(args):
    """
    Extract URL from mock call args.
    _fetch_token uses requests.Session.request(self, method, url) — unbound, args[2].
    ClientCredentialsSession.request uses super().request(method, url) — bound, args[1].
    """
    if args and not isinstance(args[0], str):
        return args[2]  # unbound: (session_instance, method, url, ...)
    return args[1]      # bound: (method, url, ...)


def make_side_effect(token_responses, api_responses):
    """
    side_effect for requests.Session.request that dispatches by URL:
      /oauth/tokens -> token_responses
      other         -> api_responses
    Handles both bound and unbound call patterns.
    """
    token_iter = iter(token_responses)
    api_iter = iter(api_responses)

    def side_effect(*args, **kwargs):
        if "/oauth/tokens" in _extract_url(args):
            return next(token_iter)
        return next(api_iter)

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

    @patch("requests.Session.request")
    def test_no_network_on_init(self, mock_request):
        ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        mock_request.assert_not_called()

    def test_token_is_none_before_first_request(self):
        self.assertIsNone(new_session()._cc_token)


class TestClientCredentialsSessionTokenFetch(TestCase):
    """Token is fetched lazily on first request."""

    @patch("requests.Session.request")
    def test_token_fetched_on_first_request(self, mock_request):
        mock_request.side_effect = make_side_effect(
            token_responses=[make_token_response("first-token")],
            api_responses=[make_api_response(200)],
        )

        session = new_session()
        session.request("GET", API_URL)

        self.assertEqual(session._cc_token, "first-token")
        self.assertIn("Bearer first-token", session.headers.get("Authorization", ""))

    @patch("requests.Session.request")
    def test_token_reused_on_subsequent_requests(self, mock_request):
        token_call_count = {"n": 0}
        base_effect = make_side_effect(
            token_responses=[make_token_response("reused-token")],
            api_responses=[make_api_response(200), make_api_response(200)],
        )

        def counting_side_effect(*args, **kwargs):
            if "/oauth/tokens" in _extract_url(args):
                token_call_count["n"] += 1
            return base_effect(*args, **kwargs)

        mock_request.side_effect = counting_side_effect

        session = new_session()
        session.request("GET", API_URL)
        session.request("GET", API_URL_2)

        self.assertEqual(token_call_count["n"], 1)

    @patch("requests.Session.request")
    def test_expires_in_passed_to_token_request(self, mock_request):
        mock_request.side_effect = make_side_effect(
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

        token_call = next(
            c for c in mock_request.call_args_list
            if "/oauth/tokens" in _extract_url(c.args)
        )
        self.assertEqual(token_call.kwargs["json"]["expires_in"], 3600)

    @patch("requests.Session.request")
    def test_expires_in_omitted_when_not_specified(self, mock_request):
        mock_request.side_effect = make_side_effect(
            token_responses=[make_token_response()],
            api_responses=[make_api_response(200)],
        )

        session = new_session()
        session.request("GET", API_URL)

        token_call = next(
            c for c in mock_request.call_args_list
            if "/oauth/tokens" in _extract_url(c.args)
        )
        self.assertNotIn("expires_in", token_call.kwargs["json"])


class TestClientCredentialsSessionTokenRefresh(TestCase):
    """Token is re-fetched on 401 and the request is retried."""

    @patch("requests.Session.request")
    def test_token_refreshed_on_401(self, mock_request):
        mock_request.side_effect = make_side_effect(
            token_responses=[make_token_response("first-token"), make_token_response("refreshed-token")],
            api_responses=[make_api_response(401), make_api_response(200)],
        )

        session = new_session()
        response = session.request("GET", API_URL)

        token_calls = [c for c in mock_request.call_args_list if "/oauth/tokens" in _extract_url(c.args)]
        api_calls = [c for c in mock_request.call_args_list if "/oauth/tokens" not in _extract_url(c.args)]
        self.assertEqual(len(token_calls), 2)
        self.assertEqual(len(api_calls), 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(session._cc_token, "refreshed-token")

    @patch("requests.Session.request")
    def test_no_infinite_retry_on_repeated_401(self, mock_request):
        """401 after token refresh is returned as-is without further retries."""
        mock_request.side_effect = make_side_effect(
            token_responses=[make_token_response("first-token"), make_token_response("refreshed-token")],
            api_responses=[make_api_response(401), make_api_response(401)],
        )

        session = new_session()
        response = session.request("GET", API_URL)

        token_calls = [c for c in mock_request.call_args_list if "/oauth/tokens" in _extract_url(c.args)]
        api_calls = [c for c in mock_request.call_args_list if "/oauth/tokens" not in _extract_url(c.args)]
        self.assertEqual(len(token_calls), 2)
        self.assertEqual(len(api_calls), 2)
        self.assertEqual(response.status_code, 401)

    @patch("requests.Session.request")
    def test_token_fetch_error_propagates(self, mock_request):
        """HTTP error on token endpoint propagates to caller with response body in message."""
        import requests as req
        error_response = MagicMock()
        error_response.ok = False
        error_response.status_code = 400
        error_response.reason = "Bad Request"
        error_response.text = '{"error":"invalid_client","error_description":"Client not found."}'

        mock_request.side_effect = make_side_effect(
            token_responses=[error_response],
            api_responses=[],
        )

        session = new_session()
        with self.assertRaises(req.exceptions.HTTPError) as ctx:
            session.request("GET", API_URL)

        self.assertIn("invalid_client", str(ctx.exception))
        api_calls = [c for c in mock_request.call_args_list if "/oauth/tokens" not in _extract_url(c.args)]
        self.assertEqual(len(api_calls), 0)


class TestZenpyClientCredentialsInit(TestCase):
    """Zenpy creates ClientCredentialsSession when client credentials are provided."""

    def test_creates_client_credentials_session(self):
        client = Zenpy(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        self.assertIsInstance(client.users.session, ClientCredentialsSession)

    def test_creates_regular_session_for_token_auth(self):
        import requests
        client = Zenpy(
            subdomain="testdomain",
            email="user@example.com",
            token="api_token",
        )
        self.assertNotIsInstance(client.users.session, ClientCredentialsSession)
        self.assertIsInstance(client.users.session, requests.Session)
