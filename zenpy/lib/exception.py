__author__ = 'facetoe'


class ZenpyException(Exception):
	"""
	A ZenpyException is raised for internal errors
	"""
	pass


class APIException(Exception):
	"""
	An APIException is raised when the API rejects a query.
	"""
	pass
