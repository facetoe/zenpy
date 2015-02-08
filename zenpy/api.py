from cStringIO import StringIO
from datetime import datetime
import json
import types
import requests
import dateutil.parser
from collections import defaultdict

__author__ = 'facetoe'

import logging
import sys

log = logging.getLogger()
log.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

logging.getLogger("requests").setLevel(logging.WARNING)


class BaseApiObject(object):
    SINGLE_GENERATORS = (
        'requester',
        'submitter',
        'assignee',
        'group',
        'content',
        'author'
    )

    def __getattribute__(self, name):
        if name.endswith("_at"):
            return dateutil.parser.parse(object.__getattribute__(self, name))

        obj = object.__getattribute__(self, name)
        if name in object.__getattribute__(self, 'SINGLE_GENERATORS'):
            if isinstance(obj, ApiCallGenerator) or isinstance(obj, types.GeneratorType):
                return obj.next()

        if isinstance(obj, list):
            if all([isinstance(o, dict) for o in obj]):
                return self.handle_dicts(obj)

        return object.__getattribute__(self, name)

    def handle_dicts(self, dicts):
        for item in dicts:
            class_name = self.api.get_class_name_from_json(item)
            yield ApiClassFactory(class_name, item, self.api)

    def is_ticket(self):
        return self.__name__ == 'Ticket'

    def is_user(self):
        return self.__name__ == 'User'

    def is_group(self):
        return self.__name__ == 'Group'

    def is_comment(self):
        return self.__name__ == 'Comment'

    def is_attachment(self):
        return self.__name__ == 'Attachment'

    def __repr__(self):
        return self.__name__.lower()


def ApiClassFactory(name, member_dict, api, BaseClass=BaseApiObject):
    def __init__(self, **kwargs):
        setattr(self, 'api', api)
        setattr(self, '__name__', name)
        for key, value in kwargs.items():
            setattr(self, key, value)
        BaseClass.__init__(self)

    def get_items(item_ids, endpoint):
        if isinstance(item_ids, int):
            item_id = item_ids
            if item_id in api.object_cache.keys():
                return api.object_cache[item_id]
            else:
                url = api.get_url(endpoint(id=item_id))

        elif isinstance(item_ids, list):
            if all([item_id in api.object_cache.keys() for item_id in item_ids]):
                return [api.object_cache[item_id] for item_id in item_ids]
            else:
                url = api.get_url(endpoint(ids=item_ids))
        else:
            raise Exception("Unknown type passed to get_items(): " + str(item_ids))

        # This is a bit hacky, pass the url to next_page so the api call won't be made until
        # the item is requested
        request_json = dict(next_page=url)
        return ApiCallGenerator(api, request_json)

    def get_attachment_content():
        yield download_file(member_dict['content_url'])

    def download_file(url):
        response = api.raw_request(url, stream=True)
        outfile = StringIO()
        for chunk in response.iter_content():
            outfile.write(chunk)
        file_contents = outfile.getvalue()
        outfile.close()
        return file_contents

    def populate_ticket():
        for user_type in ('submitter_id', 'requester_id', 'assignee_id', 'collaborator_ids'):
            item = get_items(member_dict[user_type], api.endpoint.users)
            setattr(api_object, user_type.replace('_id', ''), item)

        group = get_items(member_dict['group_id'], api.endpoint.groups)
        setattr(api_object, 'group', group)

        comments = get_items(member_dict['id'], api.endpoint.comments)
        setattr(api_object, 'comments', comments)

    def populate_attachment():
        content = get_attachment_content()
        setattr(api_object, 'content', content)

    def populate_comment():
        author = get_items(member_dict['author_id'], api.endpoint.users)
        setattr(api_object, 'author', author)

    api_object = type(name, (BaseClass,), {"__init__": __init__})(**member_dict)
    if api_object.is_ticket():
        populate_ticket()
    else:
        if api_object.id not in api.object_cache.keys():
            log.debug("Adding object to cache: " + str(api_object))
            api.object_cache.update({api_object.id: api_object})
        else:
            log.debug("Object in cache: " + str(api_object.id))

        if api_object.is_attachment():
            populate_attachment()
        elif api_object.is_comment():
            populate_comment()

    return api_object


class ApiException(Exception):
    pass


class ApiCallGenerator(object):
    api = None
    request_json = None
    position = 0
    values = list()
    multiple_results = ('tickets', 'users', 'groups', 'results', 'comments')
    single_results = ('ticket', 'user', 'group',)

    def __init__(self, api, request_json):
        self.api = api
        self.request_json = request_json
        self.values = self.get_values(request_json)

    def get_values(self, request_json):
        values = list()
        for result_type in self.multiple_results:
            if result_type in request_json:
                values = self.values + request_json[result_type]
        for result_type in self.single_results:
            if result_type in request_json:
                values.append(request_json[result_type])
        return values

    def __iter__(self):
        return self

    # Python 3 compatibility
    def __next__(self):
        return self.next()

    def make_request(self, url):
        log.info("Making generator request to: " + url)
        response = self.api.raw_request(url)
        return response.json()

    def next(self):
        # Pagination
        if self.position >= len(self.values):
            if self.request_json.get('next_page'):
                self.request_json = self.make_request(self.request_json.get('next_page'))
                self.values = self.get_values(self.request_json)
                self.position = 0
            else:
                raise StopIteration()

        if not self.values:
            raise StopIteration()

        item_json = self.values[self.position]
        self.position += 1
        class_name = self.api.get_class_name_from_json(item_json)
        return ApiClassFactory(class_name, item_json, self.api)


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
        self.endpoint = Endpoint()


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


class Endpoint(object):
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


class Zenpy(object):
    api = None

    def __init__(self, subdomain, email, token):
        self.api = Api(subdomain, email, token)

    def tickets(self, **kwargs):
        return self.api.query(self.api.endpoint.tickets(**kwargs))

    def comments(self, **kwargs):
        return self.api.query(self.api.endpoint.comments(**kwargs))

    def users(self, **kwargs):
        return self.api.query(self.api.endpoint.users(**kwargs))

    def search(self, **kwargs):
        return self.api.query(self.api.endpoint.search(**kwargs))



