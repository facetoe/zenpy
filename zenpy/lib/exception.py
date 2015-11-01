__author__ = 'facetoe'


class ZenpyException(Exception):
    """
    A ZenpyException is raised for internal errors
    """


class APIException(Exception):
    """
    An APIException is raised when the API rejects a query.
    """


class RecordNotFoundException(Exception):
    """
    A RecordNotFoundException is raised when the API cannot find a record
    """


class ZenpyCacheException(Exception):
    """
    A ZenpyCacheException is raised for errors relating the the ZenpyCache
    """
