"""
Tests for ClientCredentialsSession and Zenpy Client Credentials Grant integration.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from zenpy import Zenpy, ClientCredentialsSession


def make_token_response(access_token="test-access-token", status_code=200):
    """Create a mock response for the OAuth token endpoint."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"access_token": access_token, "token_type": "bearer"}
    response.raise_for_status = MagicMock()
    return response


def make_api_response(status_code=200):
    """Create a mock response for a Zendesk API call."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {}
    return response


class TestClientCredentialsSessionInit(TestCase):
    """ClientCredentialsSession.__init__ makes no network calls."""

    @patch("requests.post")
    def test_no_network_on_init(self, mock_post):
        ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        mock_post.assert_not_called()

    def test_token_is_none_before_first_request(self):
        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        self.assertIsNone(session._cc_token)


class TestClientCredentialsSessionTokenFetch(TestCase):
    """Token is fetched lazily on first request."""

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_token_fetched_on_first_request(self, mock_post, mock_request):
        mock_post.return_value = make_token_response("first-token")
        mock_request.return_value = make_api_response(200)

        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        session.request("GET", "https://testdomain.zendesk.com/api/v2/tickets.json")

        mock_post.assert_called_once()
        self.assertEqual(session._cc_token, "first-token")
        self.assertIn("Bearer first-token", session.headers.get("Authorization", ""))

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_token_reused_on_subsequent_requests(self, mock_post, mock_request):
        mock_post.return_value = make_token_response("reused-token")
        mock_request.return_value = make_api_response(200)

        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        session.request("GET", "https://testdomain.zendesk.com/api/v2/tickets.json")
        session.request("GET", "https://testdomain.zendesk.com/api/v2/users.json")

        self.assertEqual(mock_post.call_count, 1)

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_expires_in_passed_to_token_request(self, mock_post, mock_request):
        mock_post.return_value = make_token_response()
        mock_request.return_value = make_api_response(200)

        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
            expires_in=3600,
        )
        session.request("GET", "https://testdomain.zendesk.com/api/v2/tickets.json")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1].get("json") or call_kwargs[0][1] if len(call_kwargs[0]) > 1 else call_kwargs[1]["json"]
        self.assertEqual(body["expires_in"], 3600)

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_expires_in_omitted_when_not_specified(self, mock_post, mock_request):
        mock_post.return_value = make_token_response()
        mock_request.return_value = make_api_response(200)

        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        session.request("GET", "https://testdomain.zendesk.com/api/v2/tickets.json")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1].get("json") or call_kwargs[1]["json"]
        self.assertNotIn("expires_in", body)


class TestClientCredentialsSessionTokenRefresh(TestCase):
    """Token is re-fetched on 401 and the request is retried."""

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_token_refreshed_on_401(self, mock_post, mock_request):
        mock_post.side_effect = [
            make_token_response("first-token"),
            make_token_response("refreshed-token"),
        ]
        mock_request.side_effect = [
            make_api_response(401),
            make_api_response(200),
        ]

        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        response = session.request("GET", "https://testdomain.zendesk.com/api/v2/tickets.json")

        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(session._cc_token, "refreshed-token")

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_no_infinite_retry_on_repeated_401(self, mock_post, mock_request):
        """401 after token refresh is returned as-is without further retries."""
        mock_post.side_effect = [
            make_token_response("first-token"),
            make_token_response("refreshed-token"),
        ]
        mock_request.return_value = make_api_response(401)

        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        response = session.request("GET", "https://testdomain.zendesk.com/api/v2/tickets.json")

        # Token fetch: initial + one refresh = 2; API call: initial + one retry = 2
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(response.status_code, 401)

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_token_fetch_error_propagates(self, mock_post, mock_request):
        """HTTP error on token endpoint propagates to caller."""
        import requests as req
        error_response = MagicMock()
        error_response.raise_for_status.side_effect = req.exceptions.HTTPError("401 Unauthorized")
        mock_post.return_value = error_response

        session = ClientCredentialsSession(
            subdomain="testdomain",
            client_id="client_id",
            client_secret="client_secret",
            scope="read",
        )
        with self.assertRaises(req.exceptions.HTTPError):
            session.request("GET", "https://testdomain.zendesk.com/api/v2/tickets.json")

        mock_request.assert_not_called()


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
