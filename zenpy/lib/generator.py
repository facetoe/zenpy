__author__ = 'facetoe'

import logging
log = logging.getLogger(__name__)


class ResultGenerator(object):
	"""
	Generator for handling pagination.
	"""

	endpoint_mapping = {
		'user': 'users',
		'ticket': 'tickets',
		'group': 'groups',
		'results': 'results',
		'organization': 'organizations',
		'topic': 'topics',
		'comment': 'comments'
	}

	def __init__(self, api, result_key, _json):
		self.api = api
		self._json = _json
		self.result_key = self.endpoint_mapping[result_key]
		self.values = _json[self.result_key]
		self.position = 0

	def __iter__(self):
		return self

	def __len__(self):
		return len(self.values)

	def next(self):
		# Pagination
		if self.position >= len(self.values):
			if self._json.get('next_page'):
				self._json = self._get_as_json(self._json.get('next_page'))
				self.values = self._json[self.result_key]
				self.position = 0
			else:
				raise StopIteration()

		if not self.values:
			raise StopIteration()

		item_json = self.values[self.position]
		self.position += 1
		if 'result_type' in item_json:
			object_type = item_json.pop('result_type')
		else:
			object_type = self.result_key[:-1]  # If many objects are returned the key is plural.
		return self.api.object_manager.object_from_json(object_type, item_json)

	def _get_as_json(self, url):
		log.debug("GENERATOR: " + url)
		response = self.api._get(url)
		return response.json()
