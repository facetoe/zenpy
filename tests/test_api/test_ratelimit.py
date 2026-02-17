"""
Tests for the raise_on_ratelimit feature and enriched RatelimitBudgetExceeded.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from zenpy.lib.api import BaseApi
from zenpy.lib.exception import RateLimitError, RatelimitBudgetExceeded


def make_base_api(raise_on_ratelimit=False, ratelimit_budget=None,
                  ratelimit=None):
    """Create a minimal BaseApi instance with mocked dependencies."""
    config = dict(
        domain="zendesk.com",
        subdomain="test",
        session=MagicMock(),
        timeout=60,
        ratelimit=ratelimit,
        ratelimit_budget=ratelimit_budget,
        ratelimit_request_interval=10,
        raise_on_ratelimit=raise_on_ratelimit,
        cache=MagicMock(),
    )
    return BaseApi(**config)


def make_http_method(side_effect=None, return_value=None):
    """Create a mock http method (e.g. session.get) with a proper __name__."""
    mock = MagicMock(side_effect=side_effect, return_value=return_value)
    mock.__name__ = "get"
    return mock


def make_response(status_code=200, headers=None):
    """Create a mock requests.Response."""
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.json.return_value = {}
    return response


class TestRaiseOnRatelimit(TestCase):
    """Tests for raise_on_ratelimit=True behavior."""

    def test_raises_rate_limit_error_on_429(self):
        api = make_base_api(raise_on_ratelimit=True)
        response_429 = make_response(429, {'retry-after': '42'})
        http_method = make_http_method(return_value=response_429)

        with self.assertRaises(RateLimitError) as ctx:
            api._call_api(http_method, "https://test.zendesk.com/api/v2/tickets.json")

        self.assertEqual(ctx.exception.retry_after, 42)
        self.assertIs(ctx.exception.response, response_429)
        self.assertIn("42 seconds", str(ctx.exception))

    def test_raises_rate_limit_error_with_zero_retry_after(self):
        api = make_base_api(raise_on_ratelimit=True)
        response_429 = make_response(429, {'retry-after': '0'})
        http_method = make_http_method(return_value=response_429)

        with self.assertRaises(RateLimitError) as ctx:
            api._call_api(http_method, "https://test.zendesk.com/api/v2/tickets.json")

        self.assertEqual(ctx.exception.retry_after, 0)

    def test_raises_rate_limit_error_without_retry_after_header(self):
        api = make_base_api(raise_on_ratelimit=True)
        response_429 = make_response(429, {})
        http_method = make_http_method(return_value=response_429)

        with self.assertRaises(RateLimitError) as ctx:
            api._call_api(http_method, "https://test.zendesk.com/api/v2/tickets.json")

        self.assertEqual(ctx.exception.retry_after, 0)

    def test_does_not_raise_on_success(self):
        api = make_base_api(raise_on_ratelimit=True)
        response_200 = make_response(200, {
            'X-Rate-Limit-Remaining': '699'
        })
        http_method = make_http_method(return_value=response_200)

        result = api._call_api(http_method, "https://test.zendesk.com/api/v2/tickets.json")
        self.assertEqual(result.status_code, 200)


class TestDefaultRatelimitBehavior(TestCase):
    """Tests that default behavior (raise_on_ratelimit=False) is preserved."""

    @patch('zenpy.lib.api.sleep')
    def test_sleeps_and_retries_on_429(self, mock_sleep):
        api = make_base_api(raise_on_ratelimit=False)
        response_429 = make_response(429, {'retry-after': '2'})
        response_200 = make_response(200, {
            'X-Rate-Limit-Remaining': '699'
        })
        http_method = make_http_method(
            side_effect=[response_429, response_200])

        result = api._call_api(http_method, "https://test.zendesk.com/api/v2/tickets.json")

        self.assertEqual(result.status_code, 200)
        self.assertTrue(mock_sleep.called)

    @patch('zenpy.lib.api.sleep')
    def test_does_not_raise_rate_limit_error_by_default(self, mock_sleep):
        api = make_base_api(raise_on_ratelimit=False)
        response_429 = make_response(429, {'retry-after': '1'})
        response_200 = make_response(200, {
            'X-Rate-Limit-Remaining': '699'
        })
        http_method = make_http_method(
            side_effect=[response_429, response_200])

        try:
            api._call_api(http_method, "https://test.zendesk.com/api/v2/tickets.json")
        except RateLimitError:
            self.fail("RateLimitError should not be raised when "
                      "raise_on_ratelimit is False")


class TestRatelimitBudgetExceeded(TestCase):
    """Tests that RatelimitBudgetExceeded now carries rate limit info."""

    @patch('zenpy.lib.api.sleep')
    def test_budget_exceeded_carries_retry_after(self, mock_sleep):
        api = make_base_api(raise_on_ratelimit=False, ratelimit_budget=1)
        response_429 = make_response(429, {'retry-after': '30'})
        http_method = make_http_method(return_value=response_429)

        with self.assertRaises(RatelimitBudgetExceeded) as ctx:
            api._call_api(http_method, "https://test.zendesk.com/api/v2/tickets.json")

        self.assertEqual(ctx.exception.retry_after, 30)
        self.assertIs(ctx.exception.response, response_429)

    def test_budget_check_without_budget_does_not_raise(self):
        api = make_base_api(raise_on_ratelimit=False, ratelimit_budget=None)
        # Should not raise
        api.check_ratelimit_budget(1, retry_after=30,
                                   response=make_response(429))


class TestRateLimitErrorException(TestCase):
    """Tests for the RateLimitError exception class itself."""

    def test_attributes(self):
        response = make_response(429, {'retry-after': '10'})
        exc = RateLimitError("test message", retry_after=10,
                             response=response)
        self.assertEqual(exc.retry_after, 10)
        self.assertIs(exc.response, response)
        self.assertEqual(str(exc), "test message")

    def test_is_zenpy_exception(self):
        from zenpy.lib.exception import ZenpyException
        exc = RateLimitError("test", retry_after=0, response=None)
        self.assertIsInstance(exc, ZenpyException)


class TestRatelimitBudgetExceededException(TestCase):
    """Tests for the enriched RatelimitBudgetExceeded exception class."""

    def test_attributes_with_info(self):
        response = make_response(429)
        exc = RatelimitBudgetExceeded("budget exceeded",
                                      retry_after=15,
                                      response=response)
        self.assertEqual(exc.retry_after, 15)
        self.assertIs(exc.response, response)

    def test_backward_compatible_without_kwargs(self):
        exc = RatelimitBudgetExceeded("budget exceeded")
        self.assertIsNone(exc.retry_after)
        self.assertIsNone(exc.response)
