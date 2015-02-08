__author__ = 'facetoe'

import requests
import logging
from zenpy.api_object import ApiCallGenerator
from zenpy.exception import ApiException
from datetime import datetime
from collections import defaultdict

log = logging.getLogger(__name__)


class Api(object):
    email = None
    token = None
    subdomain = None
    protocol = None
    version = None
    base_url = None
    endpoint = None
    object_cache = defaultdict(dict)

    def __init__(self, subdomain, email, token):
        self.email = email
        self.token = token
        self.subdomain = subdomain
        self.protocol = 'https'
        self.version = 'v2'
        self.base_url = self.get_url()
        self.endpoint = ApiEndpoint()


    @staticmethod
    def get_class_name_from_json(response_json):
        if 'email' in response_json:
            return 'User'
        elif 'requester_id' in response_json:
            return 'Ticket'
        elif 'results' in response_json:
            return "SearchResult"
        elif 'author_id' in response_json:
            return 'Comment'
        elif 'file_name':
            return 'Attachment'
        elif 'name' in response_json:
            return 'Group'
        else:
            raise Exception("Unknown Type: " + str(response_json))

    def query(self, endpoint):
        log.info("Querying endpoint: " + self.get_url(endpoint=endpoint))
        response = self.raw_request(self.get_url(endpoint=endpoint))
        return ApiResponse(self, endpoint, response.json())

    def raw_request(self, url, stream=False):
        response = requests.get(url, auth=self.get_auth(), stream=stream)
        if response.status_code == 422:
            raise ApiException("Api rejected query: " + url)
        elif response.status_code != 200:
            response.raise_for_status()
        else:
            return response

    def get_url(self, endpoint=''):
        return "%(protocol)s://%(subdomain)s.zendesk.com/api/%(version)s/" % self.__dict__ + endpoint

    def get_auth(self):
        return self.email + '/token', self.token


class ApiEndpoint(object):
    __USERS = '/users/'
    __TICKETS = '/tickets/'
    __GROUPS = '/groups/'
    __SEARCH = '/search.json?query='
    __COMMENTS = '/tickets/%(id)s/comments.json'

    def search(self, **kwargs):
        renamed_kwargs = dict()
        for key, value in kwargs.iteritems():
            if isinstance(value, datetime):
                kwargs[key] = value.strftime("%Y-%m-%d")

            if '_after' in key:
                renamed_kwargs[key.replace('_after', '>')] = kwargs[key]
            elif '_before' in key:
                renamed_kwargs[key.replace('_before', '<')] = kwargs[key]
            elif '_greater_than' in key:
                renamed_kwargs[key.replace('_greater_than', '>')] = kwargs[key]
            elif '_less_than' in key:
                renamed_kwargs[key.replace('_less_than', '<')] = kwargs[key]
            else:
                renamed_kwargs.update({key + ':': value})  # Equal to , eg subject:party

        return self.__SEARCH + self.__format(**renamed_kwargs)

    def tickets(self, **kwargs):
        renamed_kwargs = dict()
        for key, value in kwargs.iteritems():
            if key == 'ids':
                renamed_kwargs[key.replace('ids', 'show_many.json?ids=')] = self.__format_many(value)
            elif key == 'sideload':
                continue
            else:
                renamed_kwargs.update({str(value) + '.json': ''})

        if 'sideload' in kwargs:
            return self.__TICKETS + self.__format_sideload(kwargs['sideload'], **renamed_kwargs)
        else:
            return self.__TICKETS + self.__format(**renamed_kwargs)

    def comments(self, **kwargs):
        return self.__COMMENTS % kwargs

    def users(self, **kwargs):
        query = 'users.json'
        for key, value in kwargs.iteritems():
            if key == 'id':
                query = self.__item(value)
            elif key == 'ids':
                query = self.__many(value)
        return self.__USERS + query

    def groups(self, **kwargs):
        query = 'groups.json'
        for key, value in kwargs.iteritems():
            if key == 'id':
                query = self.__item(value)
        return self.__GROUPS + query

    @staticmethod
    def __item(user_id):
        return str(user_id) + '.json'

    def __many(self, user_ids):
        return 'show_many.json?ids=' + self.__format_many(user_ids)

    @staticmethod
    def __format(**kwargs):
        return '+'.join(['%s%s' % (key, value) for (key, value) in kwargs.items()])

    @staticmethod
    def __format_many(items):
        return ",".join([str(i) for i in items])

    def __format_sideload(self, items, **renamed_kwargs):
        return self.__format(**renamed_kwargs) + '?include=' + self.__format_many(items)


class ApiResponse(object):
    response_json = None
    count = 0

    def __init__(self, api, endpoint, response_json):
        self.response_json = response_json
        self.endpoint = endpoint
        self.api = api

        if 'count' in self.response_json:
            self.count = self.response_json['count']

    def items(self):
        return ApiCallGenerator(self.api, self.response_json)




