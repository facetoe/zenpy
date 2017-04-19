from datetime import datetime, timedelta

from zenpy.lib.util import as_plural
from zenpy.lib.object_manager import object_from_json

__author__ = 'facetoe'

import logging

log = logging.getLogger(__name__)


class BaseResultGenerator(object):
    """
    Base class for result generators. Subclasses should implement process_page() to populate the values array. 
    """

    def __init__(self, api, response_json):
        self.api = api
        self._response_json = response_json
        self.update_attrs()
        self.values = []
        self.position = 0

    def process_page(self):
        """ Subclasses should do whatever processing is necessary and return a list of the results. """
        raise NotImplemented("You must implement process page when subclassing BaseGenerator.")

    def next(self):
        if self.values is None:
            self.values = self.process_page()
        if self.position >= len(self.values):
            self.handle_pagination()
        if len(self.values) < 1:
            raise StopIteration()
        zenpy_object = self.values[self.position]
        self.position += 1
        return zenpy_object

    def handle_pagination(self):
        """ Handle retrieving and processing the next page of results. """
        self._response_json = self.get_next_page()
        self.update_attrs()
        self.position = 0
        self.values = self.process_page()

    def update_attrs(self):
        """ Add attributes such as count/end_time that can be present """
        for key, value in self._response_json.items():
            if key != 'results' and type(value) not in (list, dict):
                setattr(self, key, value)

    def get_next_page(self):
        """ Retrieve the next page of results. """
        url = self._response_json.get('next_page', None)
        if url is None:
            raise StopIteration()
        log.debug("GENERATOR: " + url)
        response = self.api._get(url, raw_response=True)
        return response.json()

    def __iter__(self):
        return self

    def __len__(self):
        return self.count

    def __next__(self):
        return self.next()


class ResultGenerator(BaseResultGenerator):
    """ Generic result generator. """

    def __init__(self, api, response_json, object_type=None, zenpy_objects=None):
        super(ResultGenerator, self).__init__(api, response_json)
        self.values = zenpy_objects or None
        self.object_type = object_type or self.api.object_type

    def process_page(self):
        response_objects = self.api._deserialize(self._response_json)
        return response_objects[as_plural(self.object_type)]

    def get_next_page(self):
        end_time = self._response_json.get('end_time', None)
        # If we are calling an incremental API, make sure to honour the restrictions
        if end_time:
            # Incremental APIs return values in blocks of 1000 and the count value is
            # decremented by 1000 for each block that is consumed. If we have < 1000
            # then there is nothing left to retrieve.
            if self._response_json.get('count', 0) < 1000:
                raise StopIteration

            # We can't request updates from an incremental api if the
            # start_time value is less than 5 minutes in the future.
            if (datetime.fromtimestamp(int(end_time)) + timedelta(minutes=5)) > datetime.now():
                raise StopIteration
        return super(ResultGenerator, self).get_next_page()


class SearchResultGenerator(BaseResultGenerator):
    """ Result generator for search queries. """

    def process_page(self):
        search_results = list()
        for object_json in self._response_json['results']:
            object_type = object_json.pop('result_type')
            search_results.append(object_from_json(self.api, object_type, object_json))
        return search_results