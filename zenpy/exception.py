__author__ = 'facetoe'


class ApiException(Exception):
    pass


class NoResult(ApiException):
    pass

class TooManyResults(ApiException):
    pass