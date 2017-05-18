import collections
from abc import abstractmethod
from datetime import datetime, timedelta

from zenpy.lib.util import as_plural

__author__ = 'facetoe'

import logging

log = logging.getLogger(__name__)


class BaseResultGenerator(collections.Iterable):
    """
    Base class for result generators. Subclasses should implement process_page()
    and return a list of results. 
    """

    def __init__(self, response_handler, response_json):
        self.response_handler = response_handler
        self._response_json = response_json
        self.values = None
        self.position = 0
        self.update_attrs()

    @abstractmethod
    def process_page(self):
        """ Subclasses should do whatever processing is necessary and return a list of the results. """

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
        response = self.response_handler.api._get(url, raw_response=True)
        return response.json()

    def __iter__(self):
        return self

    def __len__(self):
        return self.count

    def __next__(self):
        return self.next()


class ZendeskResultGenerator(BaseResultGenerator):
    """ Generic result generator. """

    def __init__(self, response_handler, response_json, response_objects=None, object_type=None):
        super(ZendeskResultGenerator, self).__init__(response_handler, response_json)
        self.object_type = object_type or self.response_handler.api.object_type
        self.values = response_objects or None

    def process_page(self):
        response_objects = self.response_handler.deserialize(self._response_json)
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
        return super(ZendeskResultGenerator, self).get_next_page()


class SearchResultGenerator(BaseResultGenerator):
    """ Result generator for search queries. """

    def process_page(self):
        search_results = list()
        for object_json in self._response_json['results']:
            object_type = object_json.pop('result_type')
            search_results.append(self.response_handler.api._object_mapping.object_from_json(object_type, object_json))
        return search_results


class ChatResultGenerator(BaseResultGenerator):
    """
    Generator for ChatApi objects 
    """

    def process_page(self):
        return self.response_handler.deserialize(self._response_json)


class ViewResultGenerator(BaseResultGenerator):
    def process_page(self):
        return self.response_handler.deserialize(self._response_json)
