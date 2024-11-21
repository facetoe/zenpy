from __future__ import division

import re
from abc import abstractmethod
from datetime import datetime, timedelta

from zenpy.lib.util import as_plural, as_singular
from zenpy.lib.exception import SearchResponseLimitExceeded

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

import six
from math import ceil

__author__ = 'facetoe'

import logging

log = logging.getLogger(__name__)


class BaseResultGenerator(Iterable):
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
        """ Subclasses should do whatever processing is
        necessary and return a list of the results. """

    def next(self):
        if self.values is None:
            self.values = self.process_page()
        if self.position >= len(self.values):
            self.handle_pagination()
        if len(self.values) < 1 or self.position >= len(self.values):
            raise StopIteration()
        zenpy_object = self.values[self.position]
        self.position += 1
        return zenpy_object

    def handle_pagination(self, page_num=None, page_size=None):
        """ Handle retrieving and processing the next page of results. """
        self._response_json = self.get_next_page(page_num=page_num,
                                                 page_size=page_size)
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
        response = self.response_handler.api._get(url,
                                                  raw_response=True,
                                                  params=params)
        return response.json()

    def process_url(self, page_num, page_size, url):
        """ When slicing, remove the per_page and page parameters and
        pass to requests in the params dict """
        params = dict()
        if page_num is not None:
            url = re.sub(r'page=\d+', '', url)
            params['page'] = page_num
        if page_size is not None:
            url = re.sub(r'per_page=\d+', '', url)
            params['per_page'] = page_size
        return params, url

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._handle_slice(item)
        raise TypeError("only slices are supported!")

    def _handle_slice(self, slice_object):
        if self._has_sliced:
            raise NotImplementedError(
                "the current slice implementation does not support multiple accesses!"
            )
        start, stop, page_size = slice_object.start or 0, \
                                 slice_object.stop or len(self), \
                                 slice_object.step or 100
        if any((val < 0 for val in (start, stop, page_size))):
            raise ValueError(
                "negative values not supported in slice operations!")

        next_page = self._response_json.get("next_page")
        if next_page and 'incremental' in next_page:
            raise NotImplementedError(
                "the current slice implementation does not support incremental APIs!"
            )

        if self._response_json.get("before_cursor", None):
            raise NotImplementedError(
                "cursor based pagination cannot be sliced!")

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

        if six.PY2:
            min_page = int(min_page)
            max_page = int(max_page)

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
    """ Generic result generator for offset pagination. """
    def __init__(self,
                 response_handler,
                 response_json,
                 response_objects=None,
                 object_type=None):
        super(ZendeskResultGenerator, self).__init__(response_handler,
                                                     response_json)
        self.object_type = object_type or self.response_handler.api.object_type
        self.values = response_objects or self.process_page() or None

    def process_page(self):
        response_objects = self.response_handler.deserialize(
            self._response_json)
        return response_objects[as_plural(self.object_type)] if as_plural(self.object_type) in response_objects \
            else response_objects[as_singular(self.object_type)]

    def get_next_page(self, page_num=None, page_size=None):
        end_time = self._response_json.get('end_time', None)
        # If we are calling an incremental API, make sure to honour the restrictions
        if end_time:
            # We can't request updates from an incremental api if the
            # start_time value is less than 5 minutes in the future.
            if (datetime.fromtimestamp(int(end_time)) +
                    timedelta(minutes=5)) > datetime.now():
                raise StopIteration
        # No more pages to request
        if self._response_json.get("end_of_stream") is True:
            raise StopIteration
        return super(ZendeskResultGenerator,
                     self).get_next_page(page_num, page_size)


class SearchResultGenerator(BaseResultGenerator):
    """ Result generator for search queries. """
    def process_page(self):
        search_results = list()
        for object_json in self._response_json['results']:
            object_type = object_json.pop('result_type')
            search_results.append(
                self.response_handler.api._object_mapping.object_from_json(
                    object_type, object_json))
        return search_results

    def get_next_page(self, page_num, page_size):
        try:
            return super(SearchResultGenerator,
                         self).get_next_page(page_num, page_size)
        except SearchResponseLimitExceeded:
            log.error(
                'This search has resulted in more results than Zendesk allows. '
                'We got what we could.'
            )
            raise StopIteration()


class CursorResultsGenerator(BaseResultGenerator):
    """
    Generator for iterable endpoint results with cursor
    """

    def get_next_page(self):
        """ Retrieve the next page of results. """
        meta = self._response_json.get('meta')
        if meta and meta.get('has_more'):
            url = self._response_json.get('links').get('next')
            log.debug('There are more results via url={}, retrieving'.format(url))
            response = self.response_handler.api._get(url, raw_response=True)
            new_json = response.json()
            if hasattr(self, 'object_type')\
                    and len(new_json.get(as_plural(self.object_type))) == 0:
                """ 
                    Probably a bug: when the total amount is a
                    multiple of the page size,the very last page
                    comes empty.
                """
                log.debug('Empty page has got, stopping iteration')
                raise StopIteration()
            else:
                return new_json
        else:
            log.debug('No more results available, stopping iteration')
            raise StopIteration()

    def handle_pagination(self):
        """ Handle retrieving and processing the next page of results. """
        self._response_json = self.get_next_page()
        self.values.extend(self.process_page())


class GenericCursorResultsGenerator(CursorResultsGenerator):
    """ Generic result generator for cursor pagination. """
    def __init__(self,
                 response_handler,
                 response_json,
                 response_objects=None,
                 object_type=None):
        super(GenericCursorResultsGenerator, self).__init__(response_handler,
                                                     response_json)
        self.object_type = object_type or self.response_handler.api.object_type
        self.values = response_objects or self.process_page() or None

    def process_page(self):
        response_objects = self.response_handler.deserialize(
            self._response_json)
        return response_objects[as_plural(self.object_type)]


class SearchExportResultGenerator(CursorResultsGenerator):
    """
    Generator for Search Export endpoint results
    """
    def process_page(self):
        search_results = list()
        for object_json in self._response_json['results']:
            object_type = object_json.pop('result_type')
            search_results.append(
                self.response_handler.api._object_mapping.object_from_json(
                    object_type, object_json))
        return search_results


class WebhookInvocationsResultGenerator(CursorResultsGenerator):
    """
    Generator for Webhook Invocations endpoint
    """
    def process_page(self):
        search_results = list()
        for object_json in self._response_json['invocations']:
            search_results.append(
                self.response_handler.api._object_mapping.object_from_json(
                    'invocation', object_json))
        return search_results


class WebhooksResultGenerator(CursorResultsGenerator):
    """
    Generator for Webhooks list
    """
    def process_page(self):
        search_results = list()
        for object_json in self._response_json['webhooks']:
            search_results.append(
                self.response_handler.api._object_mapping.object_from_json(
                    'webhook', object_json))
        return search_results


class TicketCursorGenerator(ZendeskResultGenerator):
    """
    Generator for cursor based incremental export
    endpoints for ticket and ticket_audit objects.
    """
    def __init__(self, response_handler, response_json, object_type):
        super(TicketCursorGenerator, self).__init__(response_handler,
                                                    response_json,
                                                    response_objects=None,
                                                    object_type=object_type)
        self.next_page_attr = 'after_url'

    def __reversed__(self):
        # Flip the direction we grab pages.
        self.next_page_attr = 'before_url' \
            if self.next_page_attr == 'after_url' else 'after_url'

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


class JiraLinkGenerator(ZendeskResultGenerator):
    def __init__(self, response_handler, response_json, response):
        # The Jira links API does not provide a next_page in the JSON response.
        # Save the raw requests response to support filtering (e.g. ticket_id or
        # issue_id) during pagination.
        self.response = response
        super(JiraLinkGenerator, self).__init__(response_handler,
                                                response_json,
                                                response_objects=None,
                                                object_type='links')
        self.next_page_attr = 'since_id'

    def get_next_page(self, page_num=None, page_size=None):
        if self._response_json.get('total', 0) < 1:
            raise StopIteration()

        url = self.response.url

        # The since_id param is exclusive. Use the last id of the current page as
        # the since_id for the next page.
        since_id = str(self._response_json['links'][-1]['id'])

        if 'since_id' in url:
            # Replace the previous since_id parameter.
            url = re.sub(r'since_id=\d+', 'since_id={}'.format(since_id), url)
        else:
            if len(url.split('?')) > 1:
                # Add since_id to existing query parameters
                url += '&since_id={}'.format(since_id)
            else:
                # Add since_id as the first and only query parameter
                url += '?since_id={}'.format(since_id)

        # Save the raw requests response again.
        self.response = self.response_handler.api._get(url, raw_response=True)
        return self.response.json()

    def _handle_slice(self, slice_object):
        raise NotImplementedError(
            "the current Jira Links implementation does not support incremental APIs!"
        )


class ChatResultGenerator(BaseResultGenerator):
    """
    Generator for ChatApi objects
    """
    def __init__(self, response_handler, response_json):
        super(ChatResultGenerator, self).__init__(response_handler,
                                                  response_json)
        self.next_page_attr = 'next_url'

    def process_page(self):
        return self.response_handler.deserialize(self._response_json)


class ChatIncrementalResultGenerator(BaseResultGenerator):
    """
    Generator for Chat Incremental Api objects
    """
    def __init__(self, response_handler, response_json):
        super(ChatIncrementalResultGenerator,
              self).__init__(response_handler, response_json)
        self.next_page_attr = 'next_page'

    def process_page(self):
        return self.response_handler.deserialize(self._response_json)


class ViewResultGenerator(BaseResultGenerator):
    def process_page(self):
        return self.response_handler.deserialize(self._response_json)
