from __future__ import division

import collections
import re
from abc import abstractmethod
from datetime import datetime, timedelta

from future.standard_library import install_aliases

from zenpy.lib.util import as_plural

install_aliases()
from math import ceil

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
        self._has_sliced = False
        self.next_page_attr = 'next_page'

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

    def handle_pagination(self, page_num=None, page_size=None):
        """ Handle retrieving and processing the next page of results. """
        self._response_json = self.get_next_page(page_num=page_num, page_size=page_size)
        self.update_attrs()
        self.position = 0
        self.values = self.process_page()

    def update_attrs(self):
        """ Add attributes such as count/end_time that can be present """
        for key, value in self._response_json.items():
            if key != 'results' and type(value) not in (list, dict):
                setattr(self, key, value)

    def get_next_page(self, page_num, page_size):
        """ Retrieve the next page of results. """
        url = self._response_json.get(self.next_page_attr, None)
        if url is None:
            raise StopIteration()
        params, url = self.process_url(page_num, page_size, url)
        response = self.response_handler.api._get(url, raw_response=True, params=params)
        return response.json()

    def process_url(self, page_num, page_size, url):
        """ When slicing, remove the per_page and page parameters and pass to requests in the params dict """
        params = dict()
        if page_num is not None:
            url = re.sub('page=\d+', '', url)
            params['page'] = page_num
        if page_size is not None:
            url = re.sub('per_page=\d+', '', url)
            params['per_page'] = page_size
        return params, url

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._handle_slice(item)
        raise TypeError("only slices are supported!")

    def _handle_slice(self, slice_object):
        if self._has_sliced:
            raise NotImplementedError("the current slice implementation does not support multiple accesses!")
        start, stop, page_size = slice_object.start or 0, \
                                 slice_object.stop or len(self), \
                                 slice_object.step or 100
        if any((val < 0 for val in (start, stop, page_size))):
            raise ValueError("negative values not supported in slice operations!")

        next_page = self._response_json.get("next_page")
        if next_page and 'incremental' in next_page:
            raise NotImplementedError("the current slice implementation does not support incremental APIs!")

        if self._response_json.get("before_cursor", None):
            raise NotImplementedError("cursor based pagination cannot be sliced!")

        if self.values is None:
            self.values = self.process_page()

        values_length = len(self.values)
        if start > values_length or stop > values_length:
            result = self._retrieve_slice(start, stop, page_size)
        else:
            result = self.values[start:stop]
        self._has_sliced = True
        return result

    def _retrieve_slice(self, start, stop, page_size):
        # Calculate our range of pages.
        min_page = ceil(start / page_size)
        max_page = ceil(stop / page_size) + 1

        # Calculate the lower and upper bounds for the final slice.
        padding = ((max_page - min_page) - 1) * page_size
        lower = start % page_size or page_size
        upper = (stop % page_size or page_size) + padding

        # If we can use these objects, use them.
        consume_first_page = False
        if start <= len(self.values):
            consume_first_page = True

        # Gather all the objects in the range we want.
        to_slice = list()
        for i, page_num in enumerate(range(min_page, max_page)):
            if i == 0 and consume_first_page:
                to_slice.extend(self.values)
            else:
                self.handle_pagination(page_num=page_num, page_size=page_size)
                to_slice.extend(self.values)

        # Finally return the range of objects the user requested.
        return to_slice[lower:upper]

    def __iter__(self):
        return self

    def __len__(self):
        if hasattr(self, 'count'):
            return self.count
        elif self.values is not None:
            return len(self.values)
        else:
            return 0

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

    def get_next_page(self, page_num=None, page_size=None):
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
        return super(ZendeskResultGenerator, self).get_next_page(page_num, page_size)


class SearchResultGenerator(BaseResultGenerator):
    """ Result generator for search queries. """

    def process_page(self):
        search_results = list()
        for object_json in self._response_json['results']:
            object_type = object_json.pop('result_type')
            search_results.append(self.response_handler.api._object_mapping.object_from_json(object_type, object_json))
        return search_results

class DynamicContentResultGenerator(BaseResultGenerator):
    """ Result generator for search queries. """

    def process_page(self):
        search_results = list()
        for object_json in self._response_json['items']:
            object_type = 'dynamic_content_item'
            search_results.append(self.response_handler.api._object_mapping.object_from_json(object_type, object_json))
        return search_results


class TicketAuditGenerator(ZendeskResultGenerator):
    def __init__(self, response_handler, response_json):
        super(TicketAuditGenerator, self).__init__(response_handler, response_json,
                                                   response_objects=None,
                                                   object_type='audit')
        self.next_page_attr = 'after_url'

    def get_next_page(self, page_num=None, page_size=None):
        return super(TicketAuditGenerator, self).get_next_page()

    def __reversed__(self):
        # Flip the direction we grab pages.
        self.next_page_attr = 'before_url' if self.next_page_attr == 'after_url' else 'after_url'

        # Special case for when the generator is reversed before consuming any values.
        if self.values is None:
            self.values = list(self.process_page())
        # Not all values were consumed, begin returning items at position -1.
        elif self.position != 0:
            self.values = list(self.values[:self.position - 2])
            self.position = 0
        else:
            self.handle_pagination()
        return iter(self)


class ChatResultGenerator(BaseResultGenerator):
    """
    Generator for ChatApi objects
    """

    def __init__(self, response_handler, response_json):
        super(ChatResultGenerator, self).__init__(response_handler, response_json)
        self.next_page_attr = 'next_url'

    def process_page(self):
        return self.response_handler.deserialize(self._response_json)


class ViewResultGenerator(BaseResultGenerator):
    def process_page(self):
        return self.response_handler.deserialize(self._response_json)
