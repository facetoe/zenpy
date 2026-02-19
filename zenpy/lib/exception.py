__author__ = 'facetoe'


class ZenpyException(Exception):
    """
    A ``ZenpyException`` is raised for internal errors.
    """


class ZenpyCacheException(ZenpyException):
    """
    A ``ZenpyCacheException`` is raised for errors relating the the :class:`ZenpyCache`.
    """


class RateLimitError(ZenpyException):
    """
    A ``RateLimitError`` is raised when the Zendesk API returns a 429 status code
    and ``raise_on_ratelimit`` is enabled. It carries the rate limit information
    from Zendesk so callers can handle retries on their own (e.g. with Celery).

    :param retry_after: seconds to wait before retrying (from ``Retry-After`` header)
    :param response: the raw :class:`requests.Response` object
    """
    def __init__(self, message, retry_after, response):
        super(RateLimitError, self).__init__(message)
        self.retry_after = retry_after
        self.response = response


class RatelimitBudgetExceeded(ZenpyException):
    """
    A ``RatelimitBudgetExceeded`` is raised when the ratelimit_budget has been spent.

    :param retry_after: seconds remaining until the rate limit resets (if available)
    :param response: the raw :class:`requests.Response` object (if available)
    """
    def __init__(self, message, retry_after=None, response=None):
        super(RatelimitBudgetExceeded, self).__init__(message)
        self.retry_after = retry_after
        self.response = response


class APIException(Exception):
    """
    An ``APIException`` is raised when the API rejects a query.
    """
    def __init__(self, *args, **kwargs):
        self.response = kwargs.pop('response', None)
        super(APIException, self).__init__(*args)


class RecordNotFoundException(APIException):
    """
    A ``RecordNotFoundException`` is raised when the API cannot find a record.
    """


class TooManyValuesException(APIException):
    """
    A ``TooManyValuesException`` is raised when too many values
    have been passed to an endpoint.
    """


class SearchResponseLimitExceeded(APIException):
    """
    A ``SearchResponseLimitExceeded`` is raised when a search has too many results

    See https://develop.zendesk.com/hc/en-us/articles/360022563994--BREAKING-New-Search-API-Result-Limits
    """
