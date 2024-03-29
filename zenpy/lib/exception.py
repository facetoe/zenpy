__author__ = 'facetoe'


class ZenpyException(Exception):
    """
    A ``ZenpyException`` is raised for internal errors.
    """


class ZenpyCacheException(ZenpyException):
    """
    A ``ZenpyCacheException`` is raised for errors relating the the :class:`ZenpyCache`.
    """


class RatelimitBudgetExceeded(ZenpyException):
    """
    A ``RatelimitBudgetExceeded`` is raised when the ratelimit_budget has been spent.
    """


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
